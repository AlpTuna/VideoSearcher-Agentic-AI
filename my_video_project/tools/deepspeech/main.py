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
    
    extraction_folder = os.path.join(input_dir, "extract_" + os.path.basename(orig_input))
    os.makedirs(extraction_folder, exist_ok=True)
    
    # 2. Extract Archive
    print(f"Extracting to {extraction_folder}...")
    command = f"tar -xvzf {orig_input} -C {extraction_folder}"
    execute_command(command)
    
    # 3. SEARCH for the files
    found_wav = None
    found_mp4 = None
    
    print("Scanning for media files...")
    for root, dirs, files in os.walk(extraction_folder):
        for file in files:
            if file.startswith("._"): continue
            
            if file.endswith(".wav"):
                found_wav = os.path.join(root, file)
            elif file.endswith(".mp4"):
                found_mp4 = os.path.join(root, file)

    if not found_wav:
        print("CRITICAL: No .wav file found in the archive!")
        sys.exit(1)
        
    print(f"Found Audio: {found_wav}")

    # 4. PREPARE AUDIO
    ready_audio = os.path.join(extraction_folder, "ready_for_deepspeech.wav")
    
    # Convert audio (Force 16kHz Mono S16LE)
    ffmpeg_cmd = f"ffmpeg -y -i {found_wav} -ar 16000 -ac 1 -c:a pcm_s16le {ready_audio}"
    execute_command(ffmpeg_cmd)

    # 5. Run DeepSpeech
    #model = "/app/deepspeech-0.9.3-models.pbmm"
    #scorer = "/app/deepspeech-0.9.3-models.scorer"
    model = "deepspeech-0.9.3-models.pbmm"
    scorer = "deepspeech-0.9.3-models.scorer"
    
    print(f"Running inference on {ready_audio}...")
    ds_cmd = [
        "deepspeech", 
        "--model", model, 
        "--scorer", scorer, 
        "--audio", ready_audio
    ]
    
    result = subprocess.run(ds_cmd, capture_output=True)
    
    # 6. Process Transcript (THE FIX IS HERE)
    transcript_text = ""
    
    if result.returncode == 0:
        # Use errors='replace' just in case stdout has weird characters
        transcript_text = result.stdout.decode('utf-8', errors='replace')
        print("Success! Transcript generated.")
    else:
        # Use errors='replace' to prevent UnicodeDecodeError on crash logs
        error_msg = result.stderr.decode('utf-8', errors='replace')
        print("!!! DeepSpeech Failed !!!")
        print(error_msg)
        transcript_text = f"ERROR LOG:\n{error_msg}"

    # 7. Package Output
    transcript_filename = "transcript.txt"
    transcript_path = os.path.join(output_dir, transcript_filename)
    with open(transcript_path, "w") as file:
        file.write(transcript_text)

    final_files = [transcript_filename]
    
    if found_mp4:
        final_mp4_name = os.path.basename(orig_output) + ".mp4"
        final_mp4_path = os.path.join(output_dir, final_mp4_name)
        shutil.copy(found_mp4, final_mp4_path)
        final_files.append(final_mp4_name)
    
    output_archive = orig_output + ".tar.gz"
    print(f"Creating archive {output_archive}...")
    
    cwd = os.getcwd()
    os.chdir(output_dir)
    try:
        tar_cmd = ["tar", "-czvf", os.path.basename(output_archive)] + final_files
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