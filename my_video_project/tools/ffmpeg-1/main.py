import sys
import subprocess
import os
import argparse

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
    # We assume orig_input is the full path to the tar file
    # We extract into the directory where the output should go
    command = f"tar -xvzf {orig_input} -C {output_dir}"
    execute_command(command)
    
    timestamp_path = os.path.join(output_dir, "timestamps.txt")
    video_path = os.path.join(output_dir, "video.mp4")

    if not os.path.exists(timestamp_path):
        print(f"Error: {timestamp_path} not found.")
        sys.exit(1)

    with open(timestamp_path) as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) < 2: continue
        start, end = parts
        clip_path = f"{orig_output}_{i}.mp4"
        
        # -y forces overwrite
        command = f"ffmpeg -y -ss {start} -to {end} -i {video_path} -c copy {clip_path}"
        execute_command(command)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    main(args)
