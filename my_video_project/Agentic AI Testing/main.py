import os
import asyncio
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from agents import agent_ffmpeg1, agent_ffmpeg2, agent_deepspeech, client

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

async def main():
    # 4. The Manager Agent
    agent_manager = client.create_agent(
        name="Manager",
        instructions="""
            You are the System Orchestrator. You manage three subsystems: 'ffmpeg1', 'ffmpeg2', and 'deepspeech'.
            
            YOUR RULES:
            
            1. IF User wants to SPLIT a video given a .tar.gz file:
            - Call 'delegate_to_ffmpeg1'.

            2. IF User wants to downsize the audio and convert to .tar.gz given a video (.mp4) file:
            - Call 'delegate_to_ffmpeg2'.
            
            3. IF User wants to TRANSCRIBE a raw .mp4 video:
            - This requires a CHAIN.
            - STEP A: Call 'delegate_to_ffmpeg2' to process the .mp4.
            - STEP B: Read the output path from Step A.
            - STEP C: Call 'delegate_to_deepspeech' using the file path obtained in Step A.
            
            Always report the final output location to the user.
        """,
        tools=[delegate_to_ffmpeg1, delegate_to_ffmpeg2, delegate_to_deepspeech]
    )
    
    
    # Some example commands
    
    # Testing ffmpeg2
    #user_prompt = f"I have a video file at '{base_data_dir}/video.mp4'. Please downsize the audio"

    # Testing ffmpeg1
    user_prompt = f"I have a .tar.gz file at '{base_data_dir}/ffmpeg1_package.tar.gz'. Please split it into smaller videos based on the timestamps included in the file"
    
    
    
    print(f"\nUser: {user_prompt}")
    
    response = await agent_manager.run(user_prompt)
    
    print(f"\nManager: {response.text}")

if __name__ == "__main__":
    asyncio.run(main())