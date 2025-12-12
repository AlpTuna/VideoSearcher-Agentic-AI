import requests
import os
import json
import shutil
from typing import Annotated
import tarfile

# Configuration
DJANGO_BASE = "http://localhost:8000"

def call_ffmpeg1(
    file_path: Annotated[str, "The local path to the .tar.gz file containing video and timestamps."]
) -> str:
    """
    Directly calls the /ffmpeg1/ endpoint.
    Use this to SPLIT videos based on a timestamp file.
    """
    url = f"{DJANGO_BASE}/ffmpeg1/"
    return _send_post(url, file_path, "ffmpeg1")

def call_ffmpeg2(
    file_path: Annotated[str, "The local path to the .mp4 file."]
) -> str:
    """
    Directly calls the /ffmpeg2/ endpoint.
    Use this to PREPARE audio (extracts mono/16kHz wav) for transcription.
    Output is a .tar.gz file.
    """
    url = f"{DJANGO_BASE}/ffmpeg2/"
    return _send_post(url, file_path, "ffmpeg2")

def call_deepspeech(
    file_path: Annotated[str, "The local path to the .tar.gz file (usually output from ffmpeg2)."]
) -> str:
    """
    Directly calls the /deepspeech/ endpoint.
    Use this to TRANSCRIBE audio to text.
    """
    url = f"{DJANGO_BASE}/deepspeech/"
    return _send_post(url, file_path, "deepspeech")

def call_ffmpeg0(
    file_path: Annotated[str, "The local path to the .mp4 file."]
) -> str:
    """
    Directly calls the /ffmpeg0/ endpoint.
    Use this to extract audio from video into a package.
    Input: .mp4
    Output: .tar.gz (containing video and .wav)
    """
    url = f"{DJANGO_BASE}/ffmpeg0/"
    # We use the same helper function _send_post from the previous step
    return _send_post(url, file_path, "ffmpeg0")

def call_librosa(
    file_path: Annotated[str, "The local path to the .tar.gz file containing .mp4 and .wav."]
) -> str:
    """
    Directly calls the /librosa/ endpoint.
    Use this to generate timestamps from an audio track.
    Input: .tar.gz (video + wav)
    Output: .tar.gz (video + timestamps.txt)
    """
    url = f"{DJANGO_BASE}/librosa/"
    return _send_post(url, file_path, "librosa")

def call_grep(
    file_path: Annotated[str, "The local path to the .tar.gz file (output of Deepspeech)."],
    keyword: Annotated[str, "The specific word to search for in the transcript."]
) -> str:
    """
    Directly calls the /grep/ endpoint.
    Search for a word in the transcript.
    Input: .tar.gz (video + script) AND a keyword string.
    Output: The video file path (if found).
    """
    url = f"{DJANGO_BASE}/grep/"
    
    if not os.path.exists(file_path):
        return f"[grep Error]: Input path '{file_path}' does not exist."
        
    try:
        with open(file_path, 'rb') as f:
            # We send BOTH the file and the keyword
            payload = {'word': keyword}
            files = {'file': f}
            
            resp = requests.post(url, files=files, data=payload)
            
            try:
                data = resp.json()
                if resp.status_code == 200:
                    return f"[grep Success]: Word found. Video retrieved at: {data.get('output_location')}"
                else:
                    return f"[grep Failed]: {data.get('logs', resp.text)}"
            except:
                return f"[grep Error]: Server returned non-JSON response."
    except Exception as e:
        return f"[grep System Error]: {str(e)}"
    
def inspect_archive(
    file_path: Annotated[str, "The local path to the .tar.gz file."]
) -> str:
    """
    Extracts a .tar.gz file and returns a list of absolute paths for all .mp4 files inside.
    Use this to see what clips were generated before processing them.
    """
    # 1. Path Translation
    if file_path.startswith("/data/"):
        file_path = file_path.replace("/data/", "./media_data/")
        
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
        
    # 2. Extract
    extract_dir = file_path + "_extracted"
    os.makedirs(extract_dir, exist_ok=True)
    
    try:
        with tarfile.open(file_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
            
        # 3. List Files
        mp4_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(".mp4"):
                    # Return absolute paths so other tools can find them easily
                    full_path = os.path.abspath(os.path.join(root, file))
                    mp4_files.append(full_path)
                    
        if not mp4_files:
            return "No .mp4 files found in the archive."
            
        # Join list into a string for the LLM to read
        return "Files found:\n" + "\n".join(mp4_files)

    except Exception as e:
        return f"Error reading archive: {str(e)}"

def save_to_highlights(
    file_path: Annotated[str, "The local path to the .mp4 file that matched."]
) -> str:
    """
    Copies a specific .mp4 file to the './Agentic AI Testing/final_highlights' folder.
    Use this when a clip matches the search criteria.
    """
    # 1. Path Translation (Docker -> Local)
    if file_path.startswith("/data/"):
        file_path = file_path.replace("/data/", "./media_data/")
    
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    
    if not file_path.endswith(".mp4"):
        return f"Error: Invalid file format. expected a .mp4 file, but got {os.path.basename(file_path)}. You must save the ORIGINAL video clip, not the transcript package."

    # 2. Setup Custom Output Folder
    # We now point explicitly to your Agentic AI Testing folder
    highlights_dir = "./Agentic AI Testing/final_highlights"
    os.makedirs(highlights_dir, exist_ok=True)

    # 3. Copy File
    filename = os.path.basename(file_path)
    dest_path = os.path.join(highlights_dir, filename)
    
    try:
        shutil.copy(file_path, dest_path)
        return f"Success: Clip saved to {dest_path}"
    except Exception as e:
        return f"Error saving clip: {str(e)}"

# --- Helper (Internal) ---
def _send_post(url, fpath, tool_name):
    if not os.path.exists(fpath):
        return f"[{tool_name} Error]: File {fpath} not found."
    
    try:
        with open(fpath, 'rb') as f:
            resp = requests.post(url, files={'file': f})
            try:
                data = resp.json()
                if resp.status_code == 200:
                    # Return the Output Location so the next agent knows where to look
                    return f"[{tool_name} Success]: Output saved at: {data.get('output_location')}"
                else:
                    return f"[{tool_name} Failed]: Logs: {data.get('logs', resp.text)}"
            except:
                return f"[{tool_name} Error]: Non-JSON response from server."
    except Exception as e:
        return f"[{tool_name} System Error]: {str(e)}"