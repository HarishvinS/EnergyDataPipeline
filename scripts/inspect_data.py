import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('C:/Users/haris/Github/EnergyDataPipeline/data/Plant_1_Generation_Data.csv')

# Basic inspection
print("Dataset Shape:", df.shape)
print("\nColumn Names:")
print(df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head())
print("\nData Types:")
print(df.dtypes)
print("\nMissing Values:")
print(df.isnull().sum())
print("\nBasic Statistics:")
print(df.describe())