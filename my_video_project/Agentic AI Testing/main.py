import os
import asyncio
import tarfile
import re
import time
import shutil
from agents import agent_ffmpeg1, agent_ffmpeg2, agent_deepspeech, agent_ffmpeg0, agent_librosa, agent_grep, client
from tools import save_to_highlights
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(project_name=os.getenv('AZURE_OPENAI_DEPLOYMENT'), output_dir="./Agentic AI Testing/emissions_data")

base_data_dir = "./Agentic\\ AI\\ Testing/test_data"

def reset_directories(dir_paths):
    """
    Deletes all contents within the specified directories but keeps the parent folders.
    Used to delete upload/output of the tasks so that they dont cram up
    """
    
    for dir_path in dir_paths:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path) # Create if it doesn't exist
            continue

        # Iterate over all files and folders inside the directory
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path) # Delete file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path) # Delete subdirectory
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path}. Reason: {e}")

def extract_path_from_text(text: str) -> str:
    """
    Extracts a Docker path (/data/...) from unstructured agent text.
    Aggressively removes trailing markdown artifacts (*, `, etc).
    """
    # Regex to capture the main path part
    match = re.search(r'(/data/[\w\-\./]+\.tar\.gz|/data/[\w\-\./]+)', text)
    if match:
        path = match.group(0).strip()
        # Strip backticks, asterisks, commas, periods, quotes from the end
        return path.rstrip(".,;:`*'\"")
    return None

# --- Delegation Tools for the Manager ---
# The Manager doesn't run the logic itself; it asks the sub-agents to do it.
async def delegate_to_ffmpeg1(task: str) -> str:
    """Send a task to the ffmpeg1 agent (Splitting)."""
    tracker.start_task("Tool: FFmpeg1 (Split)")
    try:
        response = await agent_ffmpeg1.run(task)
        return response.text
    finally:
        tracker.stop_task()

async def delegate_to_ffmpeg2(task: str) -> str:
    """Send a task to the ffmpeg2 agent (Audio Prep/Conversion)."""
    print(f"\n[System] Running ffmpeg2 on: {task}", end="", flush=True)
    tracker.start_task("Tool: FFmpeg2 (Prep)")
    try:
        response = await agent_ffmpeg2.run(task)
        return response.text
    finally:
        tracker.stop_task()

async def delegate_to_deepspeech(task: str) -> str:
    """
    Transcribe and AUTO-READ the content.
    Contains inline logic to read the file so we don't need external helpers.
    """
    print(f"\n[System] Transcribing...", end="", flush=True)
    tracker.start_task("Tool: DeepSpeech (Transcribe)")

    try:
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
    finally:
        tracker.stop_task()

async def delegate_to_ffmpeg0(task: str) -> str:
    """Send a task to the ffmpeg0 agent (General Audio Extraction)."""
    print(f"\n[System] Running Extract Audio...", end="", flush=True)
    tracker.start_task("Tool: FFmpeg0 (Extract)")
    try:
        response = await agent_ffmpeg0.run(task)
        return response.text
    finally:
        tracker.stop_task()

async def delegate_to_librosa(task: str) -> str:
    """Send a task to the Librosa agent (Timestamp Generation)."""
    print(f"\n[System] Running Timestamp Analysis...", end="", flush=True)
    tracker.start_task("Tool: Librosa (Timestamps)")
    try:
        response = await agent_librosa.run(task)
        return response.text
    finally:
        tracker.stop_task()

async def delegate_to_grep(task: str) -> str:
    """Send a task to the grep agent (Content Search)."""
    print(f"\n[System] Running Grep Search...", end="", flush=True)
    tracker.start_task("Tool: Grep (Search)")
    try:
        response = await agent_grep.run(task)
        return response.text
    finally:
        tracker.stop_task()

# --- 2. THE BATCH PROCESSOR (The Agent-Driven Loop) ---
async def delegate_to_batch_processor(folder_path: str, keyword: str) -> str:
    print(f"\n\n[Batch Processor] Starting loop on: {folder_path}")
    tracker.start_task("Tool: Batch Processor Loop")
    
    try:
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
            print(f"    > Transcribe...")
            
            # Ensure file extension
            if os.path.isdir(prep_local):
                if os.path.exists(os.path.join(prep_local, "result.tar.gz")):
                    prep_local = os.path.join(prep_local, "result.tar.gz")

            resp_trans = await agent_deepspeech.run(f"Transcribe: {prep_local}")
            trans_text = resp_trans.text

            trans_docker = extract_path_from_text(trans_text)
            if not trans_docker:
                print(f" FAILED. Agent output: {trans_text[:50]}...")
                results_table += f"| {filename} | ERROR (Transcribe) | N/A |\n"
                continue

            trans_local = trans_docker.replace("/data/", "./media_data/")
            
            # ---------------------------------------------------------
            # STEP C: SEARCH (AGENT GREP)
            # ---------------------------------------------------------
            print(f"    > Searching for '{keyword}'", end="", flush=True)
            
            grep_prompt = f"Search for the word '{keyword}' in {trans_local}"
            resp_grep = await agent_grep.run(grep_prompt)
            grep_output = resp_grep.text.lower().strip()
            
            # Determine success based on Agent response
            # (Grep agent returns "Match found" or "No")
            saved_status = "NO"
            
            if "found" in grep_output or "match" in grep_output: # Could also be "match found"
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

            # Truncate output for table
            clean_grep_output = (grep_output[:50] + '...') if len(grep_output) > 50 else grep_output
            results_table += f"| {filename} | {saved_status} | {clean_grep_output} |\n"

        print("\n[Batch Processor] Loop Complete.")
        return f"Batch Processing Complete.\n\n{results_table}"
    finally:
        tracker.stop_task()
    
async def main():
    tracker.start()
    
    # The "True Agent" Prompt: Capability-based, not Procedure-based
    agent_manager = client.create_agent(
        name = "Manager",
        instructions="""
            You are an autonomous Media Processing Orchestrator.
            Your goal is to satisfy user requests by chaining together the correct tools.

            ### CRITICAL INFRASTRUCTURE RULE (Non-Negotiable)
            The tools run in Docker and return paths starting with `/data/`.
            You run locally and see these files at `./media_data/`.
            **Action:** Whenever a tool gives you a path, IMMEDIATELY translate it:
            'replace("/data/", "./media_data/")' before using it in the next tool.

            ### YOUR TOOLBOX (Capabilities)
            1. **delegate_to_ffmpeg0**: Extracts raw audio (.wav) from a video file.
               - *Use when:* You need high-quality audio or need to prepare for timestamp analysis.
            
            2. **delegate_to_librosa**: Generates silence/activity timestamps from an audio file.
               - *Use when:* You need to know *where* to split a video. 
               - *Input:* Requires the output from ffmpeg0.

            3. **delegate_to_ffmpeg1**: Splits a video into clips based on timestamps.
               - *Use when:* The user wants to "split" or "segment" a video.
               - *Input:* Requires a package containing Video + Timestamps (usually from Librosa).

            4. **delegate_to_ffmpeg2**: Downsamples audio for transcription (16kHz mono).
               - *Use when:* You need to prepare audio for text transcription.
               - *Input:* A video file.

            5. **delegate_to_deepspeech**: Transcribes speech to text.
               - *Use when:* The user wants to know what is said in the video.
               - *Input:* Requires prepared audio (from ffmpeg2).

            6. **delegate_to_batch_processor**: Scans a folder of clips and finds specific keywords.
               - *Use when:* The user wants to find "clips containing [word]".
               - *Strategy:* This requires a folder of clips first. (Hint: Split the video first).

            ### REASONING GUIDELINES
            * **Dependency Management:** If a tool needs a specific input (e.g., Timestamps), look for another tool that generates that output (e.g., Librosa) and run that first.
            * **Chain of Thought:** Before calling tools, plan your steps. Example: "To split the video, I first need timestamps. To get timestamps, I first need audio."
        """,
        tools=[delegate_to_ffmpeg0, delegate_to_ffmpeg1, delegate_to_ffmpeg2,
               delegate_to_deepspeech, delegate_to_librosa, delegate_to_grep,
               delegate_to_batch_processor]
    )
    
    # Testing full pipeline (Implicit Reasoning Test)
    user_prompt = f"Please find all the clips containing the word 'caffeine' in {base_data_dir}/video.mp4"

    print(f"\nUser: {user_prompt}")
    
    tracker.start_task("LLM Thinking")
    response = await agent_manager.run(user_prompt)
    tracker.stop_task()
    
    print(f"\nManager: {response.text}")
    tracker.stop()

    # Cleanup
    reset_directories(["media_data/uploads", "media_data/outputs"])

if __name__ == "__main__":
    asyncio.run(main())