import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate_audio(text: str, output_path: str):
    """Generates audio from text using Gemini TTS and saves it to output_path."""
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    # Using the model as originally specified
    model = "gemini-2.5-flash-preview-tts" 
    
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

    audio_data = b""
    mime_type = None

    print(f"Generating audio for text (length: {len(text)})...")
    
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
        print("Error: No audio data generated.")
        return False

    # Determine file extension and handle WAV conversion if needed
    file_extension = mimetypes.guess_extension(mime_type) if mime_type else None
    
    # If output_path doesn't have an extension, add one
    if not os.path.splitext(output_path)[1]:
        if file_extension:
            output_path += file_extension
        else:
            output_path += ".wav"

    final_data = audio_data
    if not file_extension or file_extension == ".wav":
        if mime_type:
            final_data = convert_to_wav(audio_data, mime_type)
        else:
            # Default to some standard PCM if mime_type is missing but we have data
            final_data = convert_to_wav(audio_data, "audio/L16;rate=24000")

    save_binary_file(output_path, final_data)
    return True

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


if __name__ == "__main__":
    generate()


