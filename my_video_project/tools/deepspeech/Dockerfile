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

# 3. Install Deepspeech (Works on both Mac M1/M2/M3/M4 and Windows/Linux x86)
RUN if [ "$(uname -m)" = "aarch64" ]; then \
      echo "ARM64 (Mac) detected - Installing specific wheel..." && \
      pip install https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-cp37-cp37m-linux_aarch64.whl; \
    else \
      echo "AMD64 (Windows/Server) detected - Installing from PyPI..." && \
      pip install deepspeech==0.9.3; \
    fi

# Downloading the model and scorer
RUN curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.tflite
RUN curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer

# Install other requirements (pip install deepspeech causes problems)
# RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your script and models
COPY main.py .

CMD ["tail", "-f", "/dev/null"]