import sys
import subprocess
import os
import argparse
import shutil

def execute_command(command):
    print(f">_ {command}")
    subprocess.run(command.split(), check=True)

def main(args):
    orig_input = args['input']
    orig_output = args['output']

    print(f"SCRIPT: Processing {orig_input}")

    # 1. Setup Directories
    input_dir = os.path.dirname(orig_input)
    output_dir = os.path.dirname(orig_output)
    
    # Use a unique folder for extraction to avoid conflicts
    extraction_folder = os.path.join(input_dir, "extract_" + os.path.basename(orig_input))
    os.makedirs(extraction_folder, exist_ok=True)
    
    # 2. Extract Archive
    command = f"tar -xvzf {orig_input} -C {extraction_folder}"
    execute_command(command)
    
    # 3. SEARCH for files (Fixes the "Second Run" missing MP4 issue)
    found_wav = None
    found_mp4 = None
    
    print("Scanning extracted files...")
    for root, dirs, files in os.walk(extraction_folder):
        for file in files:
            if file.startswith("._"): continue # Ignore Mac metadata
            
            if file.endswith(".wav"):
                found_wav = os.path.join(root, file)
            elif file.endswith(".mp4"):
                found_mp4 = os.path.join(root, file)

    if not found_wav:
        print("CRITICAL: No .wav file found!")
        sys.exit(1)

    # 4. Prepare Audio (Fixes Silent/Empty Transcript issue)
    ready_audio = os.path.join(extraction_folder, "ready.wav")
    print("Converting audio to DeepSpeech format...")
    # Force 16kHz, Mono, Signed 16-bit
    ffmpeg_cmd = f"ffmpeg -y -i {found_wav} -ar 16000 -ac 1 -c:a pcm_s16le {ready_audio}"
    execute_command(ffmpeg_cmd)

    # 5. Run DeepSpeech (Fixes "u/3" Error)
    # MUST point to the /models folder defined in the Dockerfile
    #model = "deepspeech-0.9.3-models.pbmm"
    model = "deepspeech-0.9.3-models.tflite"
    scorer = "deepspeech-0.9.3-models.scorer"
    
    # Sanity check to ensure models were downloaded correctly
    if not os.path.exists(model):
        print(f"CRITICAL: Model not found at {model}. Docker build failed to download it.")
        sys.exit(1)

    print("Running inference...")
    ds_cmd = [
        "deepspeech", 
        "--model", model, 
        "--scorer", scorer, 
        "--audio", ready_audio
    ]
    
    # Capture errors so they appear in transcript.txt
    result = subprocess.run(ds_cmd, capture_output=True)
    
    transcript_text = ""
    if result.returncode == 0:
        transcript_text = result.stdout.decode('utf-8')
        print("Success! Transcript generated.")
    else:
        # If it crashes, write the crash log to the file so you can read it
        error_msg = result.stderr.decode('utf-8', errors='replace')
        print("!!! DeepSpeech Failed !!!")
        print(error_msg)
        transcript_text = f"ERROR LOG:\n{error_msg}"

    # 6. Save Transcript
    transcript_filename = "transcript.txt"
    transcript_path = os.path.join(output_dir, transcript_filename)
    with open(transcript_path, "w") as file:
        file.write(transcript_text)

    # 7. Package Output (Fixes missing MP4)
    files_to_tar = [transcript_filename]
    
    if found_mp4:
        # Rename the found MP4 to match the output name Django expects
        final_video_name = os.path.basename(orig_output) + ".mp4"
        final_video_path = os.path.join(output_dir, final_video_name)
        
        shutil.copy(found_mp4, final_video_path)
        files_to_tar.append(final_video_name)
    else:
        print("WARNING: No MP4 found in the input archive.")

    output_archive = orig_output + ".tar.gz"
    print(f"Creating archive {output_archive}...")
    
    cwd = os.getcwd()
    os.chdir(output_dir)
    try:
        tar_cmd = ["tar", "-czvf", os.path.basename(output_archive)] + files_to_tar
        subprocess.run(tar_cmd, check=True)
    finally:
        os.chdir(cwd)

    shutil.rmtree(extraction_folder)
    print("Done.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = vars(parser.parse_args())
    main(args)