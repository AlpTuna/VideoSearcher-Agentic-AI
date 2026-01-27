import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.cm as cm
import numpy as np

# --- Configuration ---
MAIN_FILE = "emissions.csv"
EMISSIONS_FOLDER = "./Agentic AI Testing/emissions_data"

# --- 1. Load & Process Main Emissions Data ---
if not os.path.exists(MAIN_FILE):
    print(f"Error: '{MAIN_FILE}' not found.")
    exit()

df = pd.read_csv(MAIN_FILE)

# Process Model Name
if 'project_name' not in df.columns:
    print("Error: 'project_name' column missing.")
    exit()
df['Model'] = df['project_name']

# --- LOCATION CORRECTION ---
if 'country_name' in df.columns:
    df['Location'] = df['country_name'].fillna('Unknown')
    df['Location'] = df['Location'].replace({
        'Türkiye': 'Turkey', 
        'Turkiye': 'Turkey',
        'Canada': 'Italy'  # Merge Canada into Italy (for some reason, one run was considered Canada)
    })
else:
    df['Location'] = 'Unknown'

# Clean data
df_main = df.dropna(subset=['Model']).copy()

# --- 2. Aggregations (Energy, Power, Emissions) ---
energy_cols = ['cpu_energy', 'gpu_energy', 'ram_energy']
power_cols = ['cpu_power', 'gpu_power', 'ram_power']
metrics = energy_cols + power_cols + ['emissions']

for m in metrics:
    if m not in df_main.columns: df_main[m] = 0

# Group by MODEL (Window 1)
avg_data_model = df_main.groupby('Model')[metrics].mean()

# Group by LOCATION (Window 2)
avg_data_location = df_main.groupby('Location')[metrics].mean()


# --- 3. Process Granular Data (Tasks) ---
print(f"Processing granular files from '{EMISSIONS_FOLDER}'...")
task_data = []

NORMALIZATION_MAP = {
    "Batch Processor": "Batch Processor Loop",
    "FFmpeg0": "Tool: FFmpeg0 (Extract)",
    "FFmpeg1": "Tool: FFmpeg1 (Split)",
    "FFmpeg2": "Tool: FFmpeg2 (Prep)",
    "DeepSpeech": "Tool: DeepSpeech",
    "Librosa": "Tool: Librosa",
    "Grep": "Tool: Grep",
    "LLM Agent": "LLM Agent Pipeline",
    "Manager": "LLM Agent Pipeline"
}

def normalize_task_name(raw_name):
    raw_lower = str(raw_name).lower()
    for key, standard_name in NORMALIZATION_MAP.items():
        if key.lower() in raw_lower:
            return standard_name
    return raw_name

for index, row in df_main.iterrows():
    run_id = row['run_id']
    model_name = row['Model']
    location_name = row['Location']
    
    granular_file = os.path.join(EMISSIONS_FOLDER, f"emissions_base_{run_id}.csv")
    
    if os.path.exists(granular_file):
        try:
            sub_df = pd.read_csv(granular_file)
            if 'task_name' in sub_df.columns and 'duration' in sub_df.columns:
                run_task_sums = {}
                for _, task_row in sub_df.iterrows():
                    clean = normalize_task_name(task_row['task_name'])
                    run_task_sums[clean] = run_task_sums.get(clean, 0) + task_row['duration']

                for t_name, t_dur in run_task_sums.items():
                    task_data.append({
                        'Model': model_name,
                        'Location': location_name,
                        'Task': t_name,
                        'Duration': t_dur
                    })
        except Exception: pass
    else:
        pass

if not task_data:
    df_time_model = pd.DataFrame()
    df_time_location = pd.DataFrame()
else:
    df_tasks = pd.DataFrame(task_data)
    df_time_model = df_tasks.pivot_table(index='Model', columns='Task', values='Duration', aggfunc='mean').fillna(0)
    df_time_location = df_tasks.pivot_table(index='Location', columns='Task', values='Duration', aggfunc='mean').fillna(0)

# --- 4. Plotting Function (Clean Titles) ---
def plot_dashboard(window_title, avg_data_df, avg_time_df, fig_num):
    # Increased width to 28 to accommodate 4 graphs
    fig, axes = plt.subplots(1, 4, figsize=(28, 7))
    plt.subplots_adjust(wspace=0.3, bottom=0.25)
    
    n = len(avg_data_df)
    bar_colors = plt.cm.tab10(np.arange(n))
    hw_colors = ['#9467bd', '#17becf', '#bcbd22']
    
    # --- GRAPH 1: Energy (Stacked) ---
    avg_data_df[energy_cols].plot(kind='bar', stacked=True, ax=axes[0], color=hw_colors, edgecolor='black', width=0.6)
    axes[0].set_title('Avg Energy Consumed (kWh)', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Energy (kWh)')
    axes[0].ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    axes[0].tick_params(axis='x', rotation=30)
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)

    # --- GRAPH 2: Power (Stacked Watts) --- 
    avg_data_df[power_cols].plot(kind='bar', stacked=True, ax=axes[1], color=hw_colors, edgecolor='black', width=0.6)
    axes[1].set_title('Avg Power Draw (Watts)', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Power (Watts)')
    axes[1].tick_params(axis='x', rotation=30)
    axes[1].grid(axis='y', linestyle='--', alpha=0.5)
    
    for c in axes[1].containers:
        labels = [f'{v.get_height():.1f}' if v.get_height() > 0.1 else '' for v in c]
        axes[1].bar_label(c, labels=labels, label_type='center', fontsize=9, color='white', weight='bold')

    # --- GRAPH 3: Emissions (Bar) ---
    bars = axes[2].bar(avg_data_df.index, avg_data_df['emissions'], color=bar_colors, edgecolor='black', width=0.6)
    axes[2].set_title('Avg Emissions (kg)', fontsize=14, fontweight='bold')
    axes[2].set_ylabel('Emissions (kg CO2eq)')
    axes[2].ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    axes[2].tick_params(axis='x', rotation=30)
    axes[2].grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars:
        h = bar.get_height()
        axes[2].text(bar.get_x()+bar.get_width()/2., h, f'{h:.2e}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
    # --- GRAPH 4: Duration (Stacked) ---
    if not avg_time_df.empty:
        avg_time_df.plot(kind='bar', stacked=True, ax=axes[3], colormap='Set2', edgecolor='black', width=0.6)
        axes[3].set_title('Avg Duration Breakdown', fontsize=14, fontweight='bold')
        axes[3].set_ylabel('Time (Seconds)')
        axes[3].tick_params(axis='x', rotation=30)
        axes[3].grid(axis='y', linestyle='--', alpha=0.5)
        
        for c in axes[3].containers:
            labels = [f'{v.get_height():.0f}s' if v.get_height() > 5 else '' for v in c]
            axes[3].bar_label(c, labels=labels, label_type='center', fontsize=8, color='black')
            
        axes[3].legend(title='Task', bbox_to_anchor=(1.02, 1), loc='upper left')

    fig.suptitle(f'{window_title} Comparison', fontsize=20, y=0.98)

# --- 5. Generate Windows ---
plot_dashboard("Model", avg_data_model, df_time_model, 1)
plot_dashboard("Location", avg_data_location, df_time_location, 2)

plt.show()