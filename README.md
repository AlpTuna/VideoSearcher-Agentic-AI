# VideoSearcher-Agentic-AI

This project uses an agentic AI architecture to extract audio, split video, transcribe content, and search for keywords within video files. The system orchestrates multiple sub-agents (FFmpeg, DeepSpeech, etc.) running in Docker containers.

## 🛠️ Installation & Setup

### 1. Prerequisites
* **Docker Desktop** (must be installed and running)
* **Python 3.10+**

### 2. Create a Virtual Environment
Isolate dependencies to prevent system conflicts.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

Ensure you have the latest pip and install the required libraries.

```bash
# Upgrade pip
pip install --upgrade pip

# Install project requirements
pip install -r requirements.txt
```

### 4. Configuration

Create a .env file in the root directory to store your API keys.

```bash
# .env file content
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=[https://your-resource.openai.azure.com/](https://your-resource.openai.azure.com/)
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
```

### 🐳 Docker Setup
Crucial Step: Before running the Python script, you must ensure the tool containers are active.

Navigate to the root directory and start each individual component using the following command:

```bash
docker-compose up --build
```

### 🚀 Running the Pipeline
Once the containers are running and the environment is active, run the main orchestrator inside the Agentic AI Testing folder.

```bash
python main.py
```

### 📂 Results
The resulting clips and logs will be automatically saved in the Agentic AI Testing/final_highlights folder.

You can monitor tool execution steps, intermediate outputs, and the LLM's reasoning process directly in the terminal.
