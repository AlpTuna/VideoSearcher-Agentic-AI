import os
import asyncio
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from agents import agent_ffmpeg1, agent_ffmpeg2, agent_deepspeech, agent_ffmpeg0, agent_librosa, agent_grep, client

base_data_dir = "./Agentic\ AI\ Testing/test_data"

# --- Delegation Tools for the Manager ---
# The Manager doesn't run the logic itself; it asks the sub-agents to do it.
async def delegate_to_ffmpeg1(task: str) -> str:
    """Send a task to the ffmpeg1 agent (Splitting)."""
    response = await agent_ffmpeg1.run(task)
    return response.text

async def delegate_to_ffmpeg2(task: str) -> str:
    """Send a task to the ffmpeg2 agent (Audio Prep/Conversion)."""
    response = await agent_ffmpeg2.run(task)
    return response.text

async def delegate_to_deepspeech(task: str) -> str:
    """Send a task to the deepspeech agent (Transcription)."""
    response = await agent_deepspeech.run(task)
    return response.text

async def delegate_to_ffmpeg0(task: str) -> str:
    """Send a task to the ffmpeg0 agent (General Audio Extraction)."""
    response = await agent_ffmpeg0.run(task)
    return response.text

async def delegate_to_librosa(task: str) -> str:
    """Send a task to the Librosa agent (Timestamp Generation)."""
    response = await agent_librosa.run(task)
    return response.text

async def delegate_to_grep(task: str) -> str:
    """Send a task to the grep agent (Content Search)."""
    response = await agent_grep.run(task)
    return response.text

async def main():
    # The Manager Agent
    agent_manager = client.create_agent(
        name="Manager",
        instructions="""
            You are the System Orchestrator. You manage six subsystems: 'ffmpeg0', 'ffmpeg1', 'ffmpeg2', 'librosa', 'deepspeech', and 'grep'.
            
            ---------------------------------------------------------
            CRITICAL PATH TRANSLATION RULE:
            The API runs in a Docker container and returns paths starting with '/data/'.
            However, YOU are running locally and see these files at '/media_data/'.

            WHENEVER you receive an 'output_location' from a tool (e.g., "/data/outputs/video_ffmpeg0"):
            1. REPLACE '/data/' with './media_data/' at the start of the string.
            2. IF the path looks like a folder (does not end in .tar.gz), APPEND '/result.tar.gz'.

            EXAMPLE:
            Input from API: "/data/outputs/video_ffmpeg0"
            Translated Path you MUST use: "./media_data/outputs/video_ffmpeg0/result.tar.gz"
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

                CRITICAL: The output folder of one step contains the input file for the next step.

                * STEP A: Extract Audio
                    - Input: The raw .mp4 file provided by the user.
                    - Action: Call 'delegate_to_ffmpeg0'.
                    - Logic: If response contains "Success", extract the 'output_location' and proceed to Step B.
                    
                * STEP B: Analyze Audio for Timestamps
                    - Input: The 'output_location' file path from Step A (this is a .tar.gz).
                    - Action: Call 'delegate_to_librosa' with this new path.
                    - Logic: If response contains "Success", extract the 'output_location' and proceed to Step C.

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
                
            ---------------------------------------------------------
            GENERAL RULE:
            Always report the final output location to the user.
        """,
        tools=[delegate_to_ffmpeg0, delegate_to_ffmpeg1, delegate_to_ffmpeg2,
               delegate_to_deepspeech, delegate_to_librosa, delegate_to_grep]
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
    user_prompt = f"Please search for the word 'caffeine' in {base_data_dir}/video.mp4"
    
    
    print(f"\nUser: {user_prompt}")
    
    response = await agent_manager.run(user_prompt)
    
    print(f"\nManager: {response.text}")

if __name__ == "__main__":
    asyncio.run(main())