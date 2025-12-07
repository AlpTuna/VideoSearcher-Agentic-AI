import librosa
import sys
import time
import math
import os
import argparse
import subprocess
import glob
import shutil

def execute_command(command):
    print(f">_ {command}")
    subprocess.run(command, shell=True, check=True)

def samples_to_timestamp(sample, is_start):
    time_in_seconds = sample / 22050
    if is_start:
        time_in_seconds = math.floor(time_in_seconds)
    else:
        time_in_seconds = math.ceil(time_in_seconds)
    # Format to HH:MM:SS
    formatted_time = time.strftime('%H:%M:%S', time.gmtime(time_in_seconds))
    return formatted_time, time_in_seconds

def main(args):
    orig_input = args['input']
    orig_output = args['output']

    print(f"SCRIPT: Input at '{orig_input}', saving output in '{orig_output}'")

    input_dir = os.path.dirname(orig_input)
    output_dir = os.path.dirname(orig_output)
    output_name = os.path.basename(orig_output)
    
    # 1. Extract Archive to Temp Directory
    temp_extract_dir = os.path.join(input_dir, "extract_librosa_" + os.path.basename(orig_input))
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    print(f"Extracting to {temp_extract_dir}...")
    try:
        execute_command(f"tar -xvzf '{orig_input}' -C '{temp_extract_dir}'")
    except Exception as e:
        print(f"Error extracting tar: {e}")
        sys.exit(1)

    # 2. Search for Audio and Video files
    audio_path = None
    video_path = None
    
    for root, dirs, files in os.walk(temp_extract_dir):
        for file in files:
            if file.startswith("._"): continue 
            
            if file.endswith(".wav"):
                audio_path = os.path.join(root, file)
            elif file.endswith(".mp4"):
                video_path = os.path.join(root, file)
    
    if not audio_path:
        print("CRITICAL: No .wav file found in archive", file=sys.stderr)
        # Clean up before exiting
        shutil.rmtree(temp_extract_dir)
        sys.exit(1)
        
    print(f"Found audio: {audio_path}")

    # 3. Load Audio with Librosa
    print("Loading audio...")
    # We explicitly return sr to pass it to get_duration
    audio, sr = librosa.load(audio_path, sr=22050, mono=True)
    
    # --- THE FIX IS HERE ---
    # In Librosa 0.10.0+, 'y' and 'sr' must be keyword arguments
    duration = librosa.get_duration(y=audio, sr=sr)
    # -----------------------
    
    max_sentence_len = 30
    min_sentence_len = 6

    min_clips_number = duration / max_sentence_len
    max_clips_number = duration / min_sentence_len
    
    # 4. Calculate Splits
    clips = []
    # If audio is very short, this loop might fail to find clips, so we handle that
    try:
        for threshold_db in range(24, 50):
            clips = librosa.effects.split(audio, top_db=threshold_db)
            print(f">_ {len(clips)} clips with {threshold_db} dB as threshold")
            if len(clips) >= min_clips_number and len(clips) < max_clips_number:
                break
    except Exception as e:
        print(f"Librosa split failed: {e}")
            
    # 5. Generate Timestamps
    timestamps_file_path = os.path.join(output_dir, "timestamps.txt")
    
    with open(timestamps_file_path, "w") as file:
        last_timestamp = "00:00:00"
        last_seconds = 0
        for i in range(len(clips)):
            c = clips[i]
            
            start_timestamp = last_timestamp
            start_seconds = last_seconds
            
            end_timestamp, end_seconds = samples_to_timestamp(c[1], False)
            clip_length = end_seconds - start_seconds
            
            if start_seconds != end_seconds and clip_length > min_sentence_len:
                file.write(f"{start_timestamp} {end_timestamp}\n")
                last_timestamp = end_timestamp
                last_seconds = end_seconds

    # 6. Package Output
    files_to_tar = ["timestamps.txt"]
    
    # Handle video if found (rename to video.mp4 for consistency)
    if video_path:
        temp_video_path = os.path.join(output_dir, "video.mp4")
        shutil.copy(video_path, temp_video_path)
        files_to_tar.append("video.mp4")
    else:
        print("Warning: No video file found to package.")

    output_archive = output_name + ".tar.gz"
    print(f"Creating archive {output_archive}...")
    
    cwd = os.getcwd()
    os.chdir(output_dir)
    try:
        tar_cmd = f"tar -czvf {output_archive} {' '.join(files_to_tar)}"
        execute_command(tar_cmd)
    finally:
        os.chdir(cwd)

    # 7. Cleanup
    print("Cleaning up...")
    if os.path.exists(timestamps_file_path): os.remove(timestamps_file_path)
    if video_path and os.path.exists(os.path.join(output_dir, "video.mp4")):
        os.remove(os.path.join(output_dir, "video.mp4"))
    
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    
    print("Done.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = vars(parser.parse_args())
    main(args)