# VideoSearcher-Agentic-AI

This project uses an agentic AI architecture to extract audio, split video, transcribe content, and search for keywords within video files. The system orchestrates multiple sub-agents (FFmpeg, DeepSpeech, etc.) running in Docker containers.

## 🛠️ Installation & Setup

### 1. Prerequisites
* **Docker Desktop** (must be installed and running)
* **Python 3.11+**
* **System Drivers**: Ensure your GPU driver is up to date. Outdated drivers can cause stability issues with CodeCarbon and Docker containers.

### 2. Clone the repository
```bash
git clone https://github.com/AlpTuna/VideoSearcher-Agentic-AI.git
cd VideoSearcher-Agentic-AI/my_video_project
```

### 3. Create a Virtual Environment
Isolate dependencies to prevent system conflicts.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 4. Install Dependencies

Ensure you have the latest pip and install the required libraries.

```bash
# Upgrade pip
pip install --upgrade pip

# Install project requirements
pip install -r requirements.txt
```

### 5. Configuration

Create a .env file inside the Agentic AI Testing folder. The Manager Agent requires these credentials to communicate with the LLM (Azure OpenAI).

```bash
touch "Agentic AI Testing/.env"
```

Content of ```Agentic AI Testing/.env```
```Ini, TOML
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
```
### 6. Agent Instructions & Prompts
The Manager Agent's logic is loaded from an external text file stored in `Agentic AI Testing/prompts_archive/` for easier editing.

**To try a new prompt experiment:**
1. Create a new text file in `Agentic AI Testing/prompts_archive/` (e.g., `manager_instruction_v3.txt`).
2. Open `main.py` and modify the `manager_instructions_txtFile` variable to point to your new file:

```python
# Example change in main.py
manager_instructions_txtFile = f"{prompts_dir}/manager_instruction_v3.txt"
```

### 7. Docker Setup
Crucial Step: The "Tools" (FFmpeg and DeepSpeech) and the Django backend run inside Docker containers. The Python script (main.py) acts as the conductor, sending commands to these containers.

1. Start Docker Desktop on your machine.

2. Build and Start the Containers from the project root (```my_video_project```):

```bash
# The --build flag ensures any changes to Dockerfiles are applied
docker-compose up --build
```
Note: On the first run, this may take a few minutes as it downloads the DeepSpeech models (~1GB). Keep this terminal window OPEN. These containers act as your "servers." Open a new terminal window for the next steps.

## 🚀 Running the Pipeline
### 1. Prepare your Input

Place your source video file (e.g., ```interview.mp4```) inside the ```Agentic AI Testing/test_data``` folder.

### 2. Run the Orchestrator

  Make sure your virtual environment is active (```source venv/bin/activate```).

```bash
# Navigate to the source folder
cd "Agentic AI Testing"

# Run the main script
python main.py
```

### 3. Execution Flow

* **Orchestrator** reads the user query (defined in main.py).
  * If you use a different .mp4 input, modify the user query
 
* **CodeCarbon Initialization**: The system automatically starts tracking energy usage and carbon emissions for your local hardware.

* **Manager Agent** breaks the query into tasks.

* **Tool Agents** execute tasks inside Docker containers:

* **Final Output**
  * Video Clips: The relevant highlights are saved to ```final_highlights/```
  * Emissions Data: The detailed energy report is saved to ```emissions_data/```

## 📂 Results & Analysis
### Output Locations

**Video Clips**: Saved in ```Agentic AI Testing/final_highlights/```

**Emission Logs**: Energy consumption data is saved in ```Agentic AI Testing/emissions_data/```

> **Note on Existing Data**: The ```emissions_data``` folder currently contains CSV files from previous test runs.
> * To analyze existing results: You can run the plot script immediately.
> * To run your own clean experiment: Please delete the contents of the ```emissions_data``` folder before running main.py again.

### Generating Analysis Plots

To visualize the energy consumption and performance metrics of the agents:

1. Ensure you have run the pipeline at least once to generate emissions.csv.

2. Run the plotting script:

```bash
# Make sure you are inside "Agentic AI Testing" folder
python plot_results.py
```
The charts will be generated, showing:

* Energy Consumption per Task (Joules/kWh)

* Task Duration (Seconds)

* Carbon Emissions (kgCO2eq)
