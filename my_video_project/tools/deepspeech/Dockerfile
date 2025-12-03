# 1. Use Python 3.7 (Required for the ARM64 DeepSpeech wheel)
FROM python:3.7-slim

# 2. Install system dependencies
# 'sox' and 'libsox-fmt-all' are often needed by DeepSpeech for audio handling
RUN apt-get update && apt-get install -y \
    tar \
    curl \
    sox \
    libsox-fmt-all \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip

# 3. Install DeepSpeech 0.9.3 from the official Mozilla GitHub Release
# This is the specific wheel that works on M1/M2/M3/M4 chips (aarch64)
RUN pip install https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-cp37-cp37m-linux_aarch64.whl

# Downloading the model and scorer
RUN curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
RUN curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer

# Install other requirements (pip install deepspeech causes problems)
# RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your script and models
COPY . .

CMD ["tail", "-f", "/dev/null"]