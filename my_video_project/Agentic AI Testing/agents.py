import os
import asyncio
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from typing import Annotated
from pydantic import Field
from tools import call_ffmpeg1, call_ffmpeg2, call_deepspeech, call_ffmpeg0, call_librosa

load_dotenv()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

client = AzureOpenAIResponsesClient(
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    deployment_name=AZURE_OPENAI_DEPLOYMENT,
    # api_version=os,environ["AZURE_OPENAI_API_VERSION" ],
    # api_key=os. environ ["AZURE_OPENAI_API_KEY"], # Optional if using AzureCliCredential
    #credential=AzureCliCredential(), # Optional, if using api_key
)

# 1. Agent: ffmpeg1
agent_ffmpeg1 = client.create_agent(
    name="ffmpeg1",
    instructions="You are the ffmpeg1 specialist. Your goal is to split videos. You only accept .tar.gz files.",
    tools=[call_ffmpeg1]
)

# 2. Agent: ffmpeg2
agent_ffmpeg2 = client.create_agent(
    name="ffmpeg2",
    instructions="You are the ffmpeg2 specialist. Your goal is to convert .mp4 files into the specific .tar.gz format required for DeepSpeech.",
    tools=[call_ffmpeg2]
)

# 3. Agent: deepspeech
agent_deepspeech = client.create_agent(
    name="deepspeech",
    instructions="You are the deepspeech specialist. Your goal is to generate text transcripts from .tar.gz files.",
    tools=[call_deepspeech]
)

agent_ffmpeg0 = client.create_agent(
    name="ffmpeg0",
    instructions="""
        You are the ffmpeg0 specialist. Your goal is to extract audio from video files.
        Input: .mp4
        Output: .tar.gz
    """,
    tools=[call_ffmpeg0]
)

agent_librosa = client.create_agent(
    name="librosa",
    instructions="""
    You are the Librosa Audio Analyst.
    Your goal is to analyze audio to generate timestamps (e.g., silence detection, beat tracking).
    
    Input Requirement: A .tar.gz file containing an .mp4 video and a .wav audio track.
    Output: A .tar.gz file containing the video and a 'timestamps.txt' file.
    """,
    tools=[call_librosa]
)