# tools/video_splitter/Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg tar && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY main.py .

# IMPORTANT: We keep this container alive so Django can talk to it.
CMD ["tail", "-f", "/dev/null"]