FROM python:3.10-slim

# Install system dependency: ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the script
COPY main.py .

# Keep container running
CMD ["tail", "-f", "/dev/null"]