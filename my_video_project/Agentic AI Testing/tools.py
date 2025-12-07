import requests
import os
import json
from typing import Annotated

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