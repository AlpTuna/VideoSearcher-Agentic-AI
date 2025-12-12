import sys
import subprocess
import os
import argparse
import shutil
import glob

def execute_command(command):
    print(f">_ {command}")
    subprocess.run(command, shell=True, check=True)

def main(args):
    orig_input = args['input']
    orig_output = args['output']
    search_word = args['word']

    print(f"SCRIPT: Searching for '{search_word}' in {orig_input}")

    input_dir = os.path.dirname(orig_input)
    output_dir = os.path.dirname(orig_output)
    output_name = os.path.basename(orig_output)
    
    # 1. Extract Archive
    temp_extract_dir = os.path.join(input_dir, "extract_grep_" + os.path.basename(orig_input))
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    try:
        execute_command(f"tar -xvzf '{orig_input}' -C '{temp_extract_dir}'")
        
        # 2. Find Transcript and Video files (Robust Search)
        transcript_path = None
        video_path = None
        
        for root, dirs, files in os.walk(temp_extract_dir):
            for file in files:
                if file.startswith("._"): continue
                
                if file == "transcript.txt":
                    transcript_path = os.path.join(root, file)
                elif file.lower().endswith(('.mp4', '.mov', '.avi')):
                    video_path = os.path.join(root, file)

        if not transcript_path:
            print("CRITICAL: No transcript.txt found!", file=sys.stderr)
            sys.exit(1)

        # 3. Perform Grep (Case-Insensitive Search)
        print(f"Reading transcript from {transcript_path}...")
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        found = False
        if search_word.lower() in content.lower():
            found = True
            print(f"MATCH FOUND: The word '{search_word}' is in the transcript.")
        else:
            print(f"NO MATCH: The word '{search_word}' is NOT in the transcript.")

        # 4. Handle Output
        if found:
            # Prepare files for the new archive
            files_to_tar = ["transcript.txt"]
            
            # Move video if it exists
            if video_path:
                shutil.copy(video_path, os.path.join(output_dir, "video.mp4"))
                files_to_tar.append("video.mp4")
            
            # Copy transcript to output dir
            shutil.copy(transcript_path, os.path.join(output_dir, "transcript.txt"))
            
            # Create Archive
            archive_name = output_name + ".tar.gz"
            cwd = os.getcwd()
            os.chdir(output_dir)
            try:
                # Create the .tar.gz with only the relevant files
                tar_cmd = f"tar -czvf {archive_name} {' '.join(files_to_tar)}"
                execute_command(tar_cmd)
            finally:
                os.chdir(cwd)
                
            # Cleanup output dir artifacts (leaving only the .tar.gz)
            if os.path.exists(os.path.join(output_dir, "transcript.txt")):
                os.remove(os.path.join(output_dir, "transcript.txt"))
            if os.path.exists(os.path.join(output_dir, "video.mp4")):
                os.remove(os.path.join(output_dir, "video.mp4"))
        
        else:
            # If not found, we dont generate the output file.
            print("Skipping output generation because word was not found.")

    finally:
        # Clean up the extraction folder
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-w", "--word", required=True) # Accepting the word
    args = vars(parser.parse_args())
    main(args)