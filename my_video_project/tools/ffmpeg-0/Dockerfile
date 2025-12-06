FROM python:3.9-slim

# Install ffmpeg as requested in requirements.sys
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the script
COPY main.py .

CMD ["tail", "-f", "/dev/null"]