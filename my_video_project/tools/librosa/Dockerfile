FROM python:3.9-slim

# 1. Install System Dependencies (from requirements.sys)
# libsndfile1 is required by SoundFile/librosa
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    libsndfile1-dev \
    tar \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install Python Dependencies (from requirements.txt)
# We install explicitly to match your versions
RUN pip install SoundFile==0.12.1 librosa==0.10.0

# 3. Copy Script
COPY main.py .

CMD ["tail", "-f", "/dev/null"]