import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from main import load_data, clean_and_transform, reshape_data, save_to_json, backup_to_file
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import seaborn as sns

# Placeholder for data
global_data = {"raw": None, "prepared": None}

def load_initial_data():
    """Load initial CSV files."""
    data_dir = filedialog.askdirectory(title="Select Data Directory")
    if not data_dir:
        return

    try:
        user_log, activity_log, component_codes = load_data()
        global_data["raw"] = (user_log, activity_log, component_codes)
        messagebox.showinfo("Success", "Initial data loaded successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data: {e}")

def clean_transform_reshape():
    """Apply cleaning, transformation, and reshaping."""
    if not global_data["raw"]:
        messagebox.showerror("Error", "No data loaded! Please load the initial dataset first.")
        return

    user_log, activity_log, component_codes = global_data["raw"]
    cleaned_data = clean_and_transform(user_log, activity_log, component_codes)
    reshaped_data = reshape_data(cleaned_data)

    # Save reshaped data
    save_to_json(reshaped_data)
    backup_to_file(reshaped_data)

    global_data["prepared"] = reshaped_data
    messagebox.showinfo("Success", "Data cleaned, transformed, reshaped, and saved!")

def analyze_data():
    """Analyze data with dynamic filters and visualize results."""
    global visualization_frame  # Ensure visualization_frame is accessible

    # Check if prepared data exists and is not empty
    if global_data["prepared"] is None or global_data["prepared"].empty:
        messagebox.showerror("Error", "No prepared data available or data is empty! Please load or prepare data first.")
        return

    prepared_data = global_data["prepared"]

    # Get filter values
    user_ids = user_filter.get().split(",") if user_filter.get() else None
    components = component_filter.get().split(",") if component_filter.get() else None
    date_range = (
        pd.to_datetime(start_date.get()) if start_date.get() else None,
        pd.to_datetime(end_date.get()) if end_date.get() else None,
    )

    # Apply filters
    filtered_data = prepared_data
    if user_ids:
        filtered_data = filtered_data[filtered_data['User_ID'].isin(map(int, user_ids))]
    if components:
        filtered_data = filtered_data[['User_ID', 'Month'] + components]
    if date_range[0] and date_range[1]:
        filtered_data = filtered_data[
            (filtered_data['Date'] >= date_range[0]) & (filtered_data['Date'] <= date_range[1])
        ]

    # Check if filtered data is valid
    if filtered_data.empty:
        messagebox.showerror("Error", "Filtered data is empty. Adjust your filters.")
        return

    # Clear existing canvas (if any)
    for widget in visualization_frame.winfo_children():
        widget.destroy()

    # Visualization Options
    selected_analysis = analysis_type.get()

    if selected_analysis == "Monthly Totals":
        # Plot graph for the first component
        component = components[0] if components else filtered_data.columns[2]
        fig, ax = plt.subplots(figsize=(10, 6))
        filtered_data.groupby('Month')[component].sum().plot(kind='bar', ax=ax)
        ax.set_title(f"Monthly Total for {component}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Total Interactions")
    elif selected_analysis == "Correlation Analysis":
        # Generate correlation heatmap
        correlation_data = filtered_data.iloc[:, 2:]  # Exclude 'User_ID' and 'Month'
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(correlation_data.corr(), annot=True, cmap="coolwarm", ax=ax)
        ax.set_title("Correlation Heatmap")

    # Show the graph in GUI
    canvas = FigureCanvasTkAgg(fig, master=visualization_frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

# GUI Layout
root = tk.Tk()
root.title("Data Analysis Tool")
root.geometry("800x600")

# Configure grid layout
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Frames
controls_frame = tk.Frame(root)
controls_frame.grid(row=0, column=0, sticky="nsew")

visualization_frame = tk.Frame(root, bg="white")
visualization_frame.grid(row=0, column=1, sticky="nsew")

root.grid_columnconfigure(1, weight=3)

# Add scrollbar to visualization frame
scrollbar = ttk.Scrollbar(visualization_frame, orient="vertical")
scrollbar.grid(row=0, column=1, sticky="ns")

# Controls Layout
tk.Button(controls_frame, text="Load Initial Dataset", command=load_initial_data).grid(row=0, column=0, pady=5, padx=5, sticky="ew")
tk.Button(controls_frame, text="Clean, Transform, and Reshape Data", command=clean_transform_reshape).grid(row=1, column=0, pady=5, padx=5, sticky="ew")

# Filters
tk.Label(controls_frame, text="Filter by User IDs (comma-separated):").grid(row=2, column=0, pady=5, padx=5, sticky="w")
user_filter = tk.Entry(controls_frame)
user_filter.grid(row=3, column=0, pady=5, padx=5, sticky="ew")

tk.Label(controls_frame, text="Filter by Components (comma-separated):").grid(row=4, column=0, pady=5, padx=5, sticky="w")
component_filter = tk.Entry(controls_frame)
component_filter.grid(row=5, column=0, pady=5, padx=5, sticky="ew")

tk.Label(controls_frame, text="Filter by Start Date (YYYY-MM-DD):").grid(row=6, column=0, pady=5, padx=5, sticky="w")
start_date = tk.Entry(controls_frame)
start_date.grid(row=7, column=0, pady=5, padx=5, sticky="ew")

tk.Label(controls_frame, text="Filter by End Date (YYYY-MM-DD):").grid(row=8, column=0, pady=5, padx=5, sticky="w")
end_date = tk.Entry(controls_frame)
end_date.grid(row=9, column=0, pady=5, padx=5, sticky="ew")

# Analysis Type Selection
tk.Label(controls_frame, text="Select Analysis Type:").grid(row=10, column=0, pady=5, padx=5, sticky="w")
analysis_type = tk.StringVar(value="Monthly Totals")
tk.OptionMenu(controls_frame, analysis_type, "Monthly Totals", "Correlation Analysis").grid(row=11, column=0, pady=5, padx=5, sticky="ew")

# Analyze Button
tk.Button(controls_frame, text="Analyze Data", command=analyze_data).grid(row=12, column=0, pady=10, padx=5, sticky="ew")

# Start the GUI
root.mainloop()
