import pandas as pd
import numpy as np
from datetime import datetime

# Load raw data
df = pd.read_csv('C:/Users/haris/Github/EnergyDataPipeline/data/Plant_1_Generation_Data.csv')

print("BEFORE CLEANING:")
print(f"Shape: {df.shape}")
print(f"Missing values: {df.isnull().sum().sum()}")

# Step-by-step cleaning (customize based on your data):

# 1. Fix datetime columns (adjust column name as needed)
if 'date' in df.columns or 'timestamp' in df.columns:
    date_col = 'date'  # or whatever your date column is called
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# 2. Remove completely empty rows
df = df.dropna(how='all')

# 3. Handle missing values in key columns
# Option A: Fill with forward fill
# df['energy_value'] = df['energy_value'].fillna(method='ffill')
# Option B: Fill with zeros
# df['energy_value'] = df['energy_value'].fillna(0)
# Option C: Drop rows with missing critical values
df = df.dropna(subset=['TOTAL_YIELD'])  # replace with your energy column

# 4. Clean column names
df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

# 5. Convert energy values to numeric
energy_cols = [col for col in df.columns if any(word in col.lower() for word in ['energy', 'power', 'generation', 'output'])]
for col in energy_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 6. Remove obvious outliers (customize thresholds)
for col in energy_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

print("\nAFTER CLEANING:")
print(f"Shape: {df.shape}")
print(f"Missing values: {df.isnull().sum().sum()}")

# Save cleaned data
df.to_csv('C:/Users/haris/Github/EnergyDataPipeline/cleaned_data/cleaned_dataset.csv', index=False)
print("\nCleaned data saved to cleaned_data/cleaned_dataset.csv")