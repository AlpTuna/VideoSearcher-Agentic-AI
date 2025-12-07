FROM python:3.9-slim

# Install tar just in case
RUN apt-get update && apt-get install -y tar && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY main.py .

CMD ["tail", "-f", "/dev/null"]