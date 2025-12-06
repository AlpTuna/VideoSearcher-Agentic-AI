import sys
import subprocess
import os
import argparse
import glob
import shutil  # Required for deleting folders

def execute_command(command):
    print(">_ " + command)
    try:
        subprocess.run(command.split(), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}", file=sys.stderr)
        raise e  # Re-raise to trigger cleanup in main

def get_command_output(command):
    print(">_ " + command)
    return subprocess.run(command.split(), capture_output=True)

def main(args):
    orig_input = args['input']
    orig_output = args['output']

    print("SCRIPT: Input at '{}', saving output in '{}'".format(args['input'], args['output']))

    input_dir = os.path.dirname(orig_input)
    output_dir = os.path.dirname(orig_output)
    output_name = os.path.basename(orig_output)
    archive_name = output_name + ".tar.gz"
    
    # 1. Create a Temporary Extraction Folder
    # This keeps the 'uploads' folder clean. We extract here, not in input_dir.
    extract_tmp_dir = os.path.join(input_dir, "temp_" + os.path.basename(orig_input))
    os.makedirs(extract_tmp_dir, exist_ok=True)

    try:
        # 2. Extract Archive into Temp Folder
        command = "tar -xvzf %s -C %s" % (orig_input, extract_tmp_dir)
        execute_command(command)
        
        # 3. VALIDATION: Search for .wav inside the temp folder
        # We ignore files starting with ._ (Mac metadata)
        search_pattern = os.path.join(extract_tmp_dir, "*.wav")
        wav_files = glob.glob(search_pattern)
        valid_wavs = [f for f in wav_files if not os.path.basename(f).startswith("._")]

        if not valid_wavs:
            print("REJECTED: No valid .wav file found inside the uploaded archive.", file=sys.stderr)
            sys.exit(1) # Triggers finally block for cleanup

        audio_path = valid_wavs[0]
        print(f"Found audio file: {audio_path}")

        # 4. Run DeepSpeech
        model = "deepspeech-0.9.3-models.tflite"
        scorer = "deepspeech-0.9.3-models.scorer"

        # Note: If models are in /app, use absolute paths:
        # model = "/app/deepspeech-0.9.3-models.tflite"
        # scorer = "/app/deepspeech-0.9.3-models.scorer"

        command = "deepspeech --model %s --scorer %s --audio %s" % (model, scorer, audio_path)
        output = get_command_output(command)
        
        transcript_text = output.stdout.decode('utf-8')
        print(transcript_text)
        
        # 5. Save Transcript to Output Dir
        with open(os.path.join(output_dir, "transcript.txt"), "w") as file:
            file.write(transcript_text)

        # 6. Handle Video File (Search inside temp folder)
        # We search for any .mp4 in the temp folder since names might not match
        mp4_files = glob.glob(os.path.join(extract_tmp_dir, "*.mp4"))
        valid_mp4s = [f for f in mp4_files if not os.path.basename(f).startswith("._")]
        
        # Define the final name for the video in output dir
        final_video_name = output_name + ".mp4"
        final_video_path = os.path.join(output_dir, final_video_name)

        video_included = False
        if valid_mp4s:
            found_mp4 = valid_mp4s[0]
            print(f"Found video file: {found_mp4}")
            # Copy from temp folder to output folder
            execute_command("cp %s %s" % (found_mp4, final_video_path))
            video_included = True
        else:
            print("Warning: No .mp4 found. Output will only contain transcript.")

        # 7. Package Output
        cwd = os.getcwd()
        os.chdir(output_dir)
        
        files_to_tar = ["transcript.txt"]
        if video_included:
            files_to_tar.append(final_video_name)
            
        tar_cmd = "tar -czvf %s %s" % (archive_name, " ".join(files_to_tar))
        execute_command(tar_cmd)
        
        # Clean up output directory artifacts (keep only the tar.gz)
        if os.path.exists("transcript.txt"):
            os.remove("transcript.txt")
        if video_included and os.path.exists(final_video_name):
            os.remove(final_video_name)
            
        os.chdir(cwd)

    except Exception as e:
        print(f"Processing Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        # 8. CLEANUP: Delete the extracted files from uploads folder
        # This runs whether the script succeeds or fails
        if os.path.exists(extract_tmp_dir):
            print(f"Cleaning up extracted files in {extract_tmp_dir}...")
            shutil.rmtree(extract_tmp_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="path to input video")
    parser.add_argument("-o", "--output", help="path to output images")
    args = vars(parser.parse_args())

    main(args)