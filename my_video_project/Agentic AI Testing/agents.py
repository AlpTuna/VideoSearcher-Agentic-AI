import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from tools import call_ffmpeg1, call_ffmpeg2, call_deepspeech, call_ffmpeg0, call_librosa, call_grep

load_dotenv()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION")

client = AzureOpenAIResponsesClient(
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    deployment_name=AZURE_OPENAI_DEPLOYMENT,
    #api_version=AZURE_OPENAI_VERSION,
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

agent_grep = client.create_agent(
    name="grep",
    instructions="""
        You are the Content Search Specialist.
        Your goal is to search for specific words inside a transcript package.
        
        You will receive a request like: "Search for the word 'finance' in /path/to/file.tar.gz"
        
        You must:
        1. Extract the file path.
        2. Extract the keyword.
        3. Call the 'call_grep' tool with these exact arguments.
    """,
    tools=[call_grep]
)