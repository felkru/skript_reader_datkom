import os
import subprocess
import re
from pathlib import Path

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def merge_audios(start_slide=None, end_slide=None):
    audio_dir = Path("results/audios")
    output_dir = Path("results/merged")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    suffix = ""
    if start_slide is not None or end_slide is not None:
        s = start_slide if start_slide is not None else "start"
        e = end_slide if end_slide is not None else "end"
        suffix = f"_{s}_to_{e}"

    output_audio = output_dir / f"merged{suffix}.ogg"
    chapters_md = output_dir / f"chapters{suffix}.md"
    metadata_file = output_dir / f"ffmetadata{suffix}.txt"
    concat_file = output_dir / f"concat_list{suffix}.txt"
    
    # Find all wav files and sort them numerically
    audio_files = list(audio_dir.glob("audio*.wav"))
    
    # Extract number and filter
    valid_files = []
    for f in audio_files:
        match = re.search(r'\d+', f.name)
        if match:
            num = int(match.group())
            if (start_slide is None or num >= start_slide) and \
               (end_slide is None or num <= end_slide):
                valid_files.append((num, f))
    
    valid_files.sort() # Sort by slide number
    
    if not valid_files:
        print(f"No audio files found in results/audios for range {start_slide} to {end_slide}")
        return

    # Prepare concat list and calculate durations for chapters
    concat_content = []
    metadata_content = [";FFMETADATA1\ntitle=Merged Skript\n"]
    md_content = ["# Chapter Markers\n"]
    
    current_time_ms = 0
    
    for i, (slide_num, file) in enumerate(valid_files):
        duration = get_audio_duration(file)
        duration_ms = int(duration * 1000)
        
        title = f"Slide {slide_num}"
        
        # Concat list — escape single quotes so the path is safe inside ffmpeg's concat format
        escaped_path = str(file.absolute()).replace("'", "'\\''")
        concat_content.append(f"file '{escaped_path}'")
        
        # FFMetadata chapter
        metadata_content.append("[CHAPTER]")
        metadata_content.append("TIMEBASE=1/1000")
        metadata_content.append(f"START={current_time_ms}")
        metadata_content.append(f"END={current_time_ms + duration_ms}")
        metadata_content.append(f"title={title}\n")
        
        # MD content
        minutes = int(current_time_ms / 60000)
        seconds = int((current_time_ms % 60000) / 1000)
        md_content.append(f"- **{minutes:02d}:{seconds:02d}**: {title}")
        
        current_time_ms += duration_ms

    # Write concat list
    with open(concat_file, "w") as f:
        f.write("\n".join(concat_content))
    
    # Write metadata file
    with open(metadata_file, "w") as f:
        f.write("\n".join(metadata_content))
        
    # Write markdown file
    with open(chapters_md, "w") as f:
        f.write("\n".join(md_content))
    
    print(f"Merging {len(valid_files)} files into {output_audio}...")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-i", str(metadata_file),
        "-map_metadata", "1",
        "-c:a", "libopus",
        str(output_audio)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Successfully merged audios!")
        print(f"Output: {output_audio}")
        print(f"Chapters MD: {chapters_md}")
        # Clean up temporary files
        concat_file.unlink()
        metadata_file.unlink()
    else:
        print("Error during merging:")
        print(result.stderr)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Merge audio files into a single ogg with chapters.")
    parser.add_argument("--start", type=int, help="Starting slide number")
    parser.add_argument("--end", type=int, help="Ending slide number")
    
    args = parser.parse_args()

    if args.start is not None and args.start < 1:
        parser.error("--start must be a positive integer")
    if args.end is not None and args.end < 1:
        parser.error("--end must be a positive integer")
    if args.start is not None and args.end is not None and args.start > args.end:
        parser.error("--start must not be greater than --end")

    merge_audios(args.start, args.end)
