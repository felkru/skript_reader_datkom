import os
import sys
from src.slides_to_text import generate
from src.text_to_speech import generate_audio

def main():
    # Configuration
    start_slide = 60
    end_slide = 120 
    slides_dir = "slides"
    text_dir = "results/texts"
    audio_dir = "results/audios"
    
    # Flags to control steps
    run_text_gen = True
    run_audio_gen = True
    
    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    if run_text_gen:
        print(f"Generating TTS texts for slides {start_slide} to {end_slide}...")
        import time
        for i in range(start_slide, end_slide + 1):
            text_file = os.path.join(text_dir, f"text{i}.txt")
            if os.path.exists(text_file):
                print(f"Slide {i} text already exists. Skipping text generation.")
            else:
                # Format the slide filename: slide_060.png
                image_name = f"slide_{i:03d}.png"
                image_path = os.path.join(slides_dir, image_name)
                
                if not os.path.exists(image_path):
                    print(f"Warning: Slide {image_path} not found. Skipping.")
                    continue
                    
                print(f"Processing slide {i} to text...")
                
                texts = generate([image_path])
                
                if texts and len(texts) > 0:
                    time.sleep(1)  # Brief pause between successful requests
                    text_content = texts[0]
                    if isinstance(text_content, list) and len(text_content) > 0:
                        text_content = text_content[0]
                    
                    with open(text_file, "w", encoding="utf-8") as f:
                        f.write(text_content)
                    print(f"Saved text for slide {i} to {text_file}")
                else:
                    print(f"Error: No text generated for slide {i}")

    if run_audio_gen:
        print(f"\nGenerating audio for slides {start_slide} to {end_slide}...")
        for i in range(start_slide, end_slide + 1):
            text_file = os.path.join(text_dir, f"text{i}.txt")
            audio_file_base = os.path.join(audio_dir, f"audio{i}")
            
            # Simple check for existing audio file (wav or mp3)
            if os.path.exists(f"{audio_file_base}.wav") or os.path.exists(f"{audio_file_base}.mp3"):
                print(f"Slide {i} audio already exists. Skipping.")
                continue

            if not os.path.exists(text_file):
                print(f"Warning: Text file {text_file} not found. Skipping audio generation for slide {i}.")
                continue

            with open(text_file, "r", encoding="utf-8") as f:
                text_content = f.read().strip()
            
            if not text_content:
                print(f"Warning: Text file {text_file} is empty. Skipping.")
                continue

            print(f"Generating audio for slide {i}...")
            success = generate_audio(text_content, audio_file_base)
            if success:
                print(f"Finished audio for slide {i}")
            else:
                print(f"Failed to generate audio for slide {i}")

if __name__ == "__main__":
    main()
