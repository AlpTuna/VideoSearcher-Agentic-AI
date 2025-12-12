import os
import asyncio
from dotenv import load_dotenv
import tarfile
import re
import time
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from agents import agent_ffmpeg1, agent_ffmpeg2, agent_deepspeech, agent_ffmpeg0, agent_librosa, agent_grep, client
from tools import inspect_archive, save_to_highlights

base_data_dir = "./Agentic\ AI\ Testing/test_data"

def log_step(clip_name, step, status, details=""):
    print(f"\n[Batch] {clip_name} | {step}: {status} {details}", end="", flush=True)

def extract_path_from_text(text: str) -> str:
    """
    Extracts a Docker path (/data/...) from unstructured agent text.
    Aggressively removes trailing markdown artifacts (*, `, etc).
    """
    # Regex to capture the main path part
    match = re.search(r'(/data/[\w\-\./]+\.tar\.gz|/data/[\w\-\./]+)', text)
    if match:
        path = match.group(0).strip()
        # FIX: Strip backticks, asterisks, commas, periods, quotes from the end
        return path.rstrip(".,;:`*'\"")
    return None

# --- Delegation Tools for the Manager ---
# The Manager doesn't run the logic itself; it asks the sub-agents to do it.
async def delegate_to_ffmpeg1(task: str) -> str:
    """Send a task to the ffmpeg1 agent (Splitting)."""
    response = await agent_ffmpeg1.run(task)
    return response.text

async def delegate_to_ffmpeg2(task: str) -> str:
    """Send a task to the ffmpeg2 agent (Audio Prep/Conversion)."""
    print(f"\n[System] Running ffmpeg2 on: {task}", end="", flush=True)
    response = await agent_ffmpeg2.run(task)
    return response.text

async def delegate_to_deepspeech(task: str) -> str:
    """
    Transcribe and AUTO-READ the content.
    Contains inline logic to read the file so we don't need external helpers.
    """
    print(f"\n[System] Transcribing...", end="", flush=True)

    # 1. Run the agent (Standard)
    response = await agent_deepspeech.run(task)
    output_text = response.text
    
    # 2. Inline Logic: Try to read the transcript file locally
    if "Success" in output_text:
        try:
            # Attempt to find the docker path in the response
            # Response format expected: "... saved at: /data/outputs/..."
            if "at: " in output_text:
                docker_path = output_text.split("at: ")[1].strip().split()[0]
                
                # Manual Path Translation (Inline)
                local_path = docker_path.replace("/data/", "./media_data/")
                
                # Verify and Read
                if os.path.exists(local_path) and local_path.endswith(".tar.gz"):
                    with tarfile.open(local_path, "r:gz") as tar:
                        # Find the first .txt file
                        txt_file = next((m for m in tar.getmembers() if m.name.endswith(".txt")), None)
                        if txt_file:
                            f = tar.extractfile(txt_file)
                            content = f.read().decode('utf-8')
                            
                            # Append the ACTUAL TEXT to the output
                            output_text += f"\n\n[TRANSCRIPT EXTRACTED]:\n{content}\n"
        except Exception as e:
            output_text += f"\n(Note: Could not auto-read transcript text: {str(e)})"

    return output_text

async def delegate_to_ffmpeg0(task: str) -> str:
    """Send a task to the ffmpeg0 agent (General Audio Extraction)."""
    print(f"\n[System] Running Extract Audio...", end="", flush=True)
    response = await agent_ffmpeg0.run(task)
    return response.text

async def delegate_to_librosa(task: str) -> str:
    """Send a task to the Librosa agent (Timestamp Generation)."""
    print(f"\n[System] Running Timestamp Analysis...", end="", flush=True)
    response = await agent_librosa.run(task)
    return response.text

async def delegate_to_grep(task: str) -> str:
    """Send a task to the grep agent (Content Search)."""
    print(f"\n[System] Running Grep Search...", end="", flush=True)
    response = await agent_grep.run(task)
    return response.text

# --- 2. THE BATCH PROCESSOR (The Agent-Driven Loop) ---
async def delegate_to_batch_processor(folder_path: str, keyword: str) -> str:
    print(f"\n\n[Batch Processor] Starting loop on: {folder_path}")
    
    # 1. Path Translation
    if folder_path.startswith("/data/"):
        folder_path = folder_path.replace("/data/", "./media_data/")
    
    if not os.path.exists(folder_path):
        return f"Error: Folder {folder_path} not found."

    # 2. Find Clips
    clips = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if f.endswith(".mp4"):
                clips.append(os.path.join(root, f))
    
    if not clips:
        return "Error: No clips found."

    print(f"[Batch Processor] Found {len(clips)} clips. Starting sequential processing...")
    
    results_table = "| Clip Name | Saved? | Transcript Excerpt |\n|---|---|---|\n"
    
    for i, clip_path in enumerate(clips):
        filename = os.path.basename(clip_path)
        print(f"\n--- [{i+1}/{len(clips)}] {filename} ---")
        
        # ---------------------------------------------------------
        # STEP A: PREP (FFMPEG2)
        # ---------------------------------------------------------
        print(f"    > Prep...", end="", flush=True)
        # We call the TOOL directly (call_ffmpeg2) or the AGENT?
        # Let's use the AGENT to maintain the pattern, but parse carefully.
        resp_prep = await agent_ffmpeg2.run(f"Prepare audio for: {clip_path}")
        prep_text = resp_prep.text
        
        prep_docker = extract_path_from_text(prep_text)
        if not prep_docker:
            print(f" FAILED. Agent output: {prep_text[:50]}...")
            results_table += f"| {filename} | ERROR (Prep) | N/A |\n"
            continue
            
        print(f" Done.")
        prep_local = prep_docker.replace("/data/", "./media_data/")

        # ---------------------------------------------------------
        # STEP B: TRANSCRIBE (DEEPSPEECH)
        # ---------------------------------------------------------
        print(f"    > Transcribe...", end="", flush=True)
        
        # Ensure file extension
        if os.path.isdir(prep_local):
            if os.path.exists(os.path.join(prep_local, "result.tar.gz")):
                prep_local = os.path.join(prep_local, "result.tar.gz")

        resp_trans = await agent_deepspeech.run(f"Transcribe: {prep_local}")
        trans_text = resp_trans.text
        #print('trans_text:', trans_text)

        trans_docker = extract_path_from_text(trans_text)
        if not trans_docker:
            print(f" FAILED. Agent output: {trans_text[:50]}...")
            results_table += f"| {filename} | ERROR (Transcribe) | N/A |\n"
            continue

        trans_local = trans_docker.replace("/data/", "./media_data/")
        
        # --- AGGRESSIVE TRANSCRIPT READING ---
        transcript_snippet = "N/A"
        try:
            target_tar = trans_local
            print(f'target_tar: ({target_tar})')
            time.sleep(0.5)
            # Handle directory output
            if os.path.isdir(target_tar):
                 if os.path.exists(os.path.join(target_tar, "result.tar.gz")):
                    target_tar = os.path.join(target_tar, "result.tar.gz")

            if os.path.exists(target_tar):
                with tarfile.open(target_tar, "r:gz") as tar:
                    # DEBUG: List contents to see what the file is actually named
                    # files_in_tar = tar.getnames() 
                    # print(f" [Files: {files_in_tar}]", end="") 

                    # 1. Try finding .txt
                    txt_file = next((m for m in tar.getmembers() if m.name.endswith(".txt")), None)
                    
                    # 2. Fallback: If no .txt, take the first file that isn't a folder
                    if not txt_file:
                        txt_file = next((m for m in tar.getmembers() if m.isfile()), None)

                    if txt_file:
                        content = tar.extractfile(txt_file).read().decode('utf-8', errors='ignore')
                        full_transcript = content
                        clean = content.replace('\n', ' ').strip()
                        transcript_snippet = (clean[:50] + '...') if len(clean) > 50 else clean
                        print(f" Done. Content: \"{transcript_snippet}\"")
                    else:
                         print(f" Done (Empty Archive).")
            else:
                print(f" Failed (File not found: {target_tar})") # this is called

        except Exception as e:
            print(f" Error Reading: {e}")

        # ---------------------------------------------------------
        # STEP C: SEARCH (PYTHON - DIRECT)
        # ---------------------------------------------------------
        # We skip the Grep Agent entirely because we already have the text!
        print(f"    > Searching for '{keyword}'...", end="", flush=True)
        
        saved_status = "NO"
        if keyword.lower() in full_transcript.lower():
            print(" MATCH! Saving...", end="")
            save_msg = save_to_highlights(clip_path)
            if "Success" in save_msg:
                print(" Saved.")
                saved_status = "YES"
            else:
                print(f" Save Failed: {save_msg}")
                saved_status = "ERROR (Save)"
        else:
            print(" No Match.")

        results_table += f"| {filename} | {saved_status} | {transcript_snippet} |\n"

    print("\n[Batch Processor] Loop Complete.")
    return f"Batch Processing Complete.\n\n{results_table}"
    
async def main():
    # The Manager Agent
    agent_manager = client.create_agent(
        name="Manager",
        instructions="""
            You are the System Orchestrator. You manage six subsystems: 'ffmpeg0', 'ffmpeg1', 'ffmpeg2', 'librosa', 'deepspeech', and 'grep'.
            
            ---------------------------------------------------------
            CRITICAL PATH TRANSLATION RULE:
            The API runs in a Docker container and returns paths starting with '/data/'.
            However, YOU are running locally and see these files at './media_data/'.

            WHENEVER you receive an 'output_location' from a tool:
            1. REPLACE '/data/' with './media_data/' at the start of the string.
            ---------------------------------------------------------

            YOUR RULES:

            1. IF User wants to EXTRACT AUDIO from a video:
                - The input has to be a .mp4 file
                - Call 'delegate_to_ffmpeg0'
            
            2. IF User wants to SPLIT a video given a .tar.gz file:
                - The input has to be a .tar.gz file that contains a compressed video file (.mp4) and a text file with timestamps (.txt)
                - Call 'delegate_to_ffmpeg1'.

            3. IF User wants to DOWNSIZE the audio and convert to .tar.gz given a video (.mp4) file:
                - The input has to be a .mp4 file
                - Call 'delegate_to_ffmpeg2'.
            
            4. IF User wants to TRANSCRIBE a video:
                - The input has to be a .tar.gz file which contains a compressed video (.mp4) and a downsampled audio (mono 16 kHz 16 bit .wav).
                - If the input is correct, call 'delegate_to_deepspeech'

            5. IF User wants to GET TIMESTAMPS of a video:
                - The input has to be a .tar.gz file which contains a video (.mp4) and its extracted audio (.wav)
                - Call 'delegate_to_librosa'

            6. IF User wants to SEARCH for a word inside a video:
                - Input: A .tar.gz file (from Deepspeech) AND a keyword.
                - Action: Construct a sentence like "Search for '[keyword]' in [TRANSLATED_PATH]"
                - Call 'delegate_to_grep' with that sentence.

            ---------------------------------------------------------
            YOUR RULES FOR COMPLEX PIPELINES (CHAIN OF THOUGHT):

            7. IF User wants to AUTO-SPLIT a raw .mp4 video (based on audio/silence):
                You must execute this Strict 3-Step Pipeline. 
                Check the result of each step. If any step fails, STOP and report the error.

                CRITICAL: The output of one step is the input file for the next step.

                * STEP A: Extract Audio
                    - Input: The raw .mp4 file provided by the user.
                    - Action: Call 'delegate_to_ffmpeg0'.
                    - Logic: If response contains "Success", extract the 'output_location' and proceed to Step B.
                    - CRITICAL: Apply Path Translation Rule (/data/ -> ./media_data/).
                    
                * STEP B: Analyze Audio for Timestamps
                    - Input: The 'output_location' file path from Step A (this is a .tar.gz).
                    - Action: Call 'delegate_to_librosa' with this new path.
                    - Logic: If response contains "Success", extract the 'output_location' and proceed to Step C.
                    - CRITICAL: Apply Path Translation Rule.

                * STEP C: Split the Video
                    - Input: The 'output_location' file path from Step B (this is a .tar.gz).
                    - Action: Call 'delegate_to_ffmpeg1' with this new path.
                    - Logic: Report the final success message and location to the user.
            
            8. IF User wants to SEARCH for a word inside a RAW .mp4 video:
                You must execute this Strict 3-Step Pipeline.
                Check the result of each step. If any step fails, STOP and report the error.

                CRITICAL: The output folder of one step contains the input file for the next step.

                * STEP A: Prepare Audio (ffmpeg2)
                    - Input: The raw .mp4 file provided by the user.
                    - Action: Call 'delegate_to_ffmpeg2'.
                    - Logic: If response contains "Success", extract the 'output_location'.
                    - TRANSLATION: Apply Path Translation Rule to this location and proceed to Step B.

                * STEP B: Transcribe (deepspeech)
                    - Input: The TRANSLATED file path from Step A.
                    - Action: Call 'delegate_to_deepspeech' with this new path.
                    - Logic: If response contains "Success", extract the 'output_location'.
                    - TRANSLATION: Apply Path Translation Rule to this location and proceed to Step C.

                * STEP C: Search (grep)
                    - Input: The TRANSLATED file path from Step B AND the keyword provided by the user.
                    - Action: Call 'delegate_to_grep' with the sentence: "Search for '[keyword]' in [TRANSLATED_PATH]".
                    - Logic: Report if the word was found or not.


            9. SMART HIGHLIGHT PIPELINE (Split Video -> Search Each Clip):
                If the user wants to "Find all clips containing [word]" or "Extract highlights from [video]":
                
                You must execute this 2-Phase Process.
                
                * PHASE 1: EXECUTE AUTO-SPLIT (Reuse Pipeline 7 logic manually)
                    A. Call 'delegate_to_ffmpeg0' (Extract Audio).
                        - Apply Translation Rule.
                    B. Call 'delegate_to_librosa' (Get Timestamps).
                        - Apply Translation Rule.
                    C. Call 'delegate_to_ffmpeg1' (Split Video).
                        - Logic: Extract the 'output_location' (this is a FOLDER of clips).
                        - TRANSLATION: Replace '/data/' with '/media_data/'. Do NOT append a filename, as we need the folder.

                * PHASE 2: BATCH PROCESS
                 A. Call 'delegate_to_batch_processor'.
                    - Arguments: Provide the FOLDER PATH from Phase 1 and the KEYWORD.
                    - This tool will handle the looping and searching for you.

                * PHASE 3: REPORT
                 - The Batch Processor will return a summary table.
                 - Simply print that table to the user.
                
            ---------------------------------------------------------
            GENERAL RULE:
            Always report the final output location to the user.
        """,
        tools=[delegate_to_ffmpeg0, delegate_to_ffmpeg1, delegate_to_ffmpeg2,
               delegate_to_deepspeech, delegate_to_librosa, delegate_to_grep,
               inspect_archive, save_to_highlights, delegate_to_batch_processor]
    )
    
    
    # Some example commands
    
    # Testing ffmpeg0
    #user_prompt = f"I have a video file at '{base_data_dir}/video.mp4'. Get me the audio of this video"
    
    # Testing ffmpeg2
    #user_prompt = f"I have a video file at '{base_data_dir}/video.mp4'. Please downsize the audio"
    #user_prompt = f"I have a video file at '{base_data_dir}/ffmpeg1_package.tar.gz'. Please downsize the audio"

    # Testing ffmpeg1
    #user_prompt = f"I have a .tar.gz file at '{base_data_dir}/ffmpeg1_package.tar.gz'. Please split it into smaller videos based on the timestamps included in the file"
    #user_prompt = f"I have a .tar.gz file at '{base_data_dir}/full_video_deepspeech.tar.gz'. Please split it into smaller videos based on the timestamps included in the file"
    
    # Testing deepspeech
    #user_prompt = f"I have a .tar.gz file at '{base_data_dir}/full_video_deepspeech.tar.gz'. Please transcribe the video inside it"
    #user_prompt = f"I have a .tar.gz file at '{base_data_dir}/ffmpeg1_package.tar.gz'. Please transcribe the video inside it"
    #user_prompt = f"Please transcribe my video at {base_data_dir}/full_video_deepspeech.tar.gz"
    
    # Testing librosa
    #user_prompt = f"Please get the timestamps of my .tar.gz file at {base_data_dir}/result.tar.gz"
    #user_prompt = f"Please get the timestamps of my .tar.gz file at {base_data_dir}/ffmpeg1_package.tar.gz"

    # Testing complex 1 (auto splitting)
    #user_prompt = f"Please auto-split the video at {base_data_dir}/video.mp4"

    # Testing complex 2 (word searching)
    #user_prompt = f"Please search for the word 'caffeine' in {base_data_dir}/video.mp4"
    
    # Testing full pipeline
    user_prompt = f"Please find all the clips containing the word 'caffeine' in {base_data_dir}/video.mp4"

    print(f"\nUser: {user_prompt}")
    
    response = await agent_manager.run(user_prompt)
    
    print(f"\nManager: {response.text}")

if __name__ == "__main__":
    asyncio.run(main())