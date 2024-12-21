import pandas as pd
import os
from pymongo import MongoClient
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Load raw data from CSV files
def load_data():
    data_dir = './data'
    user_log_path = os.path.join(data_dir, 'USER_LOG.csv')
    activity_log_path = os.path.join(data_dir, 'ACTIVITY_LOG.csv')
    component_codes_path = os.path.join(data_dir, 'COMPONENT_CODES.csv')
    user_log = pd.read_csv(user_log_path)
    activity_log = pd.read_csv(activity_log_path)
    component_codes = pd.read_csv(component_codes_path)
    return user_log, activity_log, component_codes

# Clean and merge data
def clean_and_transform(user_log, activity_log, component_codes):
    activity_log = activity_log[~activity_log['Component'].isin(['System', 'Folder'])].copy()
    user_log.rename(columns={"User Full Name *Anonymized": "User_ID"}, inplace=True)
    activity_log.rename(columns={"User Full Name *Anonymized": "User_ID"}, inplace=True)
    merged_data = pd.merge(user_log, activity_log, on="User_ID")
    return merged_data

# Reshape data for analysis
def reshape_data(merged_data):
    merged_data['Date'] = pd.to_datetime(merged_data['Date'], dayfirst=True)
    merged_data['Month'] = merged_data['Date'].dt.month

    pivot_table = merged_data.pivot_table(index=['User_ID', 'Month'], columns='Component', values='Action', aggfunc='count').fillna(0)
    pivot_table.reset_index(inplace=True)  # Reset index to ensure 'User_ID' is a column

    return pivot_table


# Save to JSON
def save_to_json(data):
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, 'cleaned_data.json')
    data.to_json(json_path, orient='records', indent=4)
    print(f"Data saved to JSON at {json_path}")

# Save to MongoDB
def save_to_mongodb(data, db_name='DataBackup', collection_name='backup'):
    client = MongoClient('localhost', 27017)
    db = client[db_name]
    collection = db[collection_name]
    data_dict = data.to_dict('records')
    collection.insert_many(data_dict)
    print("Data backed up to MongoDB.")

# Backup to CSV file
def backup_to_file(data):
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(output_dir, f'backup_{timestamp}.csv')
    data.to_csv(backup_path, index=False)
    print(f"Backup saved to file at {backup_path}")

# Load prepared data from JSON
def load_prepared_data():
    json_path = './output/cleaned_data.json'
    try:
        data = pd.read_json(json_path, orient='records')
        print(f"Prepared data loaded successfully from {json_path}")
        if 'User_ID' not in data.columns:
            print("Error: 'User_ID' column not found in prepared data.")
        return data
    except FileNotFoundError:
        print(f"File not found: {json_path}")
        return None


# Filter data by user IDs, components, and date range
def filter_data(data, user_ids=None, components=None, date_range=None):
    filtered_data = data.copy()
    if user_ids:
        filtered_data = filtered_data[filtered_data['User_ID'].isin(user_ids)]
    if components:
        filtered_data = filtered_data[[col for col in filtered_data.columns if col in components or col in ['User_ID', 'Month']]]
    if date_range:
        start_date, end_date = date_range
        filtered_data = filtered_data[(filtered_data['Date'] >= start_date) & (filtered_data['Date'] <= end_date)]
    return filtered_data

# Generate statistics
def generate_statistics(data, components):
    stats = {}
    for component in components:
        if component in data.columns:
            stats[component] = {
                'mean': data[component].mean(),
                'median': data[component].median(),
                'mode': data[component].mode().iloc[0] if not data[component].mode().empty else None
            }
    return stats

# Generate graphs
def generate_graph(data, components):
    for component in components:
        if component in data.columns:
            plt.figure(figsize=(10, 6))
            data.groupby('Month')[component].sum().plot(kind='bar')
            plt.title(f'Monthly Total for {component}')
            plt.xlabel('Month')
            plt.ylabel('Total Interactions')
            plt.show()

# Generate correlation analysis
def generate_correlation(data, components):
    correlation_data = data[components].corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_data, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Matrix')
    plt.show()

# Main function
def main():
    # Load and process data
    user_log, activity_log, component_codes = load_data()
    cleaned_data = clean_and_transform(user_log, activity_log, component_codes)
    reshaped_data = reshape_data(cleaned_data)
    
    # Save backups
    save_to_json(reshaped_data)
    save_to_mongodb(reshaped_data)
    backup_to_file(reshaped_data)

    # Load prepared data
    prepared_data = load_prepared_data()
    if prepared_data is None:
        return

    # Analyze data
    user_ids = [1, 2]
    components = ['Assignment', 'Quiz', 'Lecture']
    filtered_data = filter_data(prepared_data, user_ids=user_ids, components=components)
    
    # Generate outputs
    stats = generate_statistics(filtered_data, components)
    print("Statistics:", stats)
    generate_graph(filtered_data, components)
    generate_correlation(filtered_data, components)

if __name__ == '__main__':
    main()
