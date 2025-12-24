import sys
import subprocess
import os
import argparse

def execute_command(command):
    print(f">_ {command}")
    subprocess.run(command, shell=True, check=True)

def main(args):
    orig_input = args.input
    output_folder = args.output
    
    # 1. Create the Output Directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"SCRIPT: Processing {orig_input} -> Output Folder: {output_folder}")

    # 2. Extract
    # We extract into the directory where the output clips should go
    command = f"tar -xvzf {orig_input} -C {output_folder}"
    execute_command(command)
    
    # Paths for extracted files
    timestamp_path = os.path.join(output_folder, "timestamps.txt")
    video_path = os.path.join(output_folder, "video.mp4")

    if not os.path.exists(timestamp_path):
        print(f"Error: {timestamp_path} not found.")
        sys.exit(1)

    with open(timestamp_path) as file:
        lines = file.readlines()

    generated_clips = []

    # 3. Generate Clips
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) < 2: continue
        start, end = parts
        
        # Name the clips simply
        clip_name = f"clip_{i}.mp4"
        clip_path = os.path.join(output_folder, clip_name)
        
        # -y forces overwrite, -c copy is fast (no re-encoding)
        command = f"ffmpeg -y -ss {start} -to {end} -i {video_path} -c copy {clip_path}"
        execute_command(command)
        generated_clips.append(clip_name)

    print(f"Successfully created {len(generated_clips)} clips in {output_folder}")

    # 4. Cleanup (Delete only the extracted input files)
    print("Cleaning up intermediate source files...")
    
    # We dont delete the generated clips, because that is what we want to keep
    if os.path.exists(timestamp_path): os.remove(timestamp_path)
    if os.path.exists(video_path): os.remove(video_path)

    print("Done.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    main(args)