import sys
import subprocess
import os
import argparse
import glob

def execute_command(command):
    print(f">_ {command}")
    subprocess.run(command, shell=True, check=True)

def main(args):
    orig_input = args.input
    orig_output = args.output
    
    # Ensure output directory exists
    output_dir = os.path.dirname(orig_output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"SCRIPT: Processing {orig_input} -> {orig_output}")

    # 1. Extract
    # We extract into the directory where the output should go
    command = f"tar -xvzf {orig_input} -C {output_dir}"
    execute_command(command)
    
    # Handle filenames robustly (in case they are renamed inside)
    # But assuming standard names based on your previous tools:
    timestamp_path = os.path.join(output_dir, "timestamps.txt")
    video_path = os.path.join(output_dir, "video.mp4")

    if not os.path.exists(timestamp_path):
        print(f"Error: {timestamp_path} not found.")
        sys.exit(1)

    with open(timestamp_path) as file:
        lines = file.readlines()

    generated_clips = []

    # 2. Generate Clips
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) < 2: continue
        start, end = parts
        
        # We name the clips based on the output prefix
        # e.g. result_0.mp4, result_1.mp4
        clip_name = f"{os.path.basename(orig_output)}_{i}.mp4"
        clip_path = os.path.join(output_dir, clip_name)
        
        # -y forces overwrite, -c copy is fast (no re-encoding)
        command = f"ffmpeg -y -ss {start} -to {end} -i {video_path} -c copy {clip_path}"
        execute_command(command)
        generated_clips.append(clip_name)

    # 3. Create .tar.gz Archive
    archive_name = os.path.basename(orig_output) + ".tar.gz"
    print(f"Creating archive {archive_name} with {len(generated_clips)} clips...")

    cwd = os.getcwd()
    os.chdir(output_dir)
    try:
        if generated_clips:
            # Join filenames with spaces for the tar command
            clips_str = " ".join(generated_clips)
            tar_cmd = f"tar -czvf {archive_name} {clips_str}"
            execute_command(tar_cmd)
        else:
            print("Warning: No clips generated to archive.")
    finally:
        os.chdir(cwd)

    # 4. Cleanup (Delete individual clips and extracted input)
    print("Cleaning up intermediate files...")
    # Delete the generated clip files
    for clip in generated_clips:
        path = os.path.join(output_dir, clip)
        if os.path.exists(path):
            os.remove(path)
            
    # Delete extracted input files
    if os.path.exists(timestamp_path): os.remove(timestamp_path)
    if os.path.exists(video_path): os.remove(video_path)

    print("Done.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    main(args)