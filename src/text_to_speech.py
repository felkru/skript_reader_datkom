import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set. See .env.example.")
    return value

def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


import time
import random

def generate_audio(text: str, output_path: str, max_retries: int = 3):
    """Generates audio from text using Gemini TTS and saves it to output_path.
    
    Args:
        text: The text to convert to speech.
        output_path: The base path (without extension) for the output audio file.
        max_retries: Maximum number of retries for transient errors.
    """
    client = genai.Client(
        vertexai=True,
        project=_require_env("GCP_PROJECT_ID"),
        location=_require_env("GCP_LOCATION"),
    )

    # Use the specific gemini-2.5-flash-tts model
    model = "gemini-2.5-flash-tts" 
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"Read aloud in a warm and friendly tone:\n\n{text}"),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Charon"  # Or another voice like "Puck", "Charon", "Kore", "Fenrir"
                )
            )
        ),
    )

    print(f"Generating audio for text (length: {len(text)})...")
    
    for attempt in range(max_retries + 1):
        audio_data = b""
        mime_type = None
        
        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.parts is None:
                    continue
                    
                for part in chunk.parts:
                    if part.inline_data and part.inline_data.data:
                        audio_data += part.inline_data.data
                        if mime_type is None:
                            mime_type = part.inline_data.mime_type
                    elif part.text:
                        print(f"Model response text: {part.text}")

            if not audio_data:
                print(f"Attempt {attempt + 1}: No audio data generated.")
                if attempt < max_retries:
                    continue
                return False

            # Determine file extension and handle WAV conversion if needed
            file_extension = mimetypes.guess_extension(mime_type) if mime_type else None
            
            # If output_path doesn't have an extension, add one
            actual_output_path = output_path
            if not os.path.splitext(actual_output_path)[1]:
                if file_extension:
                    actual_output_path += file_extension
                else:
                    actual_output_path += ".wav"

            final_data = audio_data
            if mime_type and mime_type.startswith("audio/L"):
                # Raw PCM data needs a WAV header
                final_data = convert_to_wav(audio_data, mime_type)
            elif not mime_type:
                final_data = convert_to_wav(audio_data, "audio/L16;rate=24000")

            save_binary_file(actual_output_path, final_data)
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"Attempt {attempt + 1} failed: {error_msg}")
            
            # Check for transient errors
            is_transient = any(err in error_msg.lower() for err in [
                "nameresolutionerror", 
                "dns", 
                "connection", 
                "timeout", 
                "503", 
                "504", 
                "deadline exceeded"
            ])
            
            if attempt < max_retries and is_transient:
                sleep_time = (2 ** attempt) + random.random()
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                return False

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters."""
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string."""
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


if __name__ == "__main__":
    pass
