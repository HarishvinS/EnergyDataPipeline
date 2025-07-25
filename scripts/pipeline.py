import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class EnergyDataPipeline:
    def __init__(self, input_file=None, output_file=None):
        # Set default input file if not provided
        if input_file is None:
            self.input_file = '../data/Plant_1_Generation_Data.csv'
        else:
            self.input_file = input_file
            
        # Set default output file if not provided
        if output_file is None:
            self.output_file = '../cleaned_data/processed_dataset.csv'
        else:
            self.output_file = output_file
            
        self.raw_data = None
        self.cleaned_data = None
        self.processed_data = None
    
    def load_data(self):
        """Step 1: Load raw data"""
        print("Loading data...")
        self.raw_data = pd.read_csv(self.input_file)
        print(f"Loaded {len(self.raw_data)} rows")
        return self
    
    def clean_data(self):
        """Step 2: Clean data"""
        print("Cleaning data...")
        self.cleaned_data = self.raw_data.copy()
        
        # 1. Fix datetime columns
        date_col = None
        for col in self.cleaned_data.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
                
        if date_col:
            print(f"Converting {date_col} to datetime...")
            self.cleaned_data[date_col] = pd.to_datetime(self.cleaned_data[date_col], errors='coerce')
        
        # 2. Remove completely empty rows
        self.cleaned_data = self.cleaned_data.dropna(how='all')
        
        # 3. Handle missing values in key columns
        key_cols = [col for col in self.cleaned_data.columns if any(word in col.lower() 
                   for word in ['yield', 'energy', 'power', 'generation', 'output'])]
        
        if key_cols:
            print(f"Dropping rows with missing values in key columns: {key_cols}")
            self.cleaned_data = self.cleaned_data.dropna(subset=key_cols)
        
        # 4. Clean column names
        self.cleaned_data.columns = self.cleaned_data.columns.str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
        
        # 5. Convert energy values to numeric
        energy_cols = [col for col in self.cleaned_data.columns if any(word in col.lower() 
                      for word in ['energy', 'power', 'generation', 'output', 'yield'])]
        
        for col in energy_cols:
            self.cleaned_data[col] = pd.to_numeric(self.cleaned_data[col], errors='coerce')
        
        # 6. Remove obvious outliers
        for col in energy_cols:
            Q1 = self.cleaned_data[col].quantile(0.25)
            Q3 = self.cleaned_data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            self.cleaned_data = self.cleaned_data[(self.cleaned_data[col] >= lower_bound) & 
                                                 (self.cleaned_data[col] <= upper_bound)]
        
        print(f"Cleaned data: {len(self.cleaned_data)} rows remaining")
        return self
    
    def create_features(self):
        """Step 3: Create new features"""
        print("Creating features...")
        self.processed_data = self.cleaned_data.copy()
        
        # Identify date column
        date_col = None
        for col in self.processed_data.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if date_col:
            # Ensure datetime format
            if not pd.api.types.is_datetime64_any_dtype(self.processed_data[date_col]):
                self.processed_data[date_col] = pd.to_datetime(self.processed_data[date_col], errors='coerce')
            
            # Extract time components
            self.processed_data['hour'] = self.processed_data[date_col].dt.hour
            self.processed_data['day'] = self.processed_data[date_col].dt.day
            self.processed_data['month'] = self.processed_data[date_col].dt.month
            self.processed_data['year'] = self.processed_data[date_col].dt.year
            self.processed_data['dayofweek'] = self.processed_data[date_col].dt.dayofweek
            
            # Create weekend flag
            self.processed_data['is_weekend'] = self.processed_data['dayofweek'].isin([5, 6]).astype(int)
            
            print(f"Created time-based features from {date_col}")
        
        # Find energy/power columns for feature engineering
        energy_cols = [col for col in self.processed_data.columns if any(word in col.lower() 
                      for word in ['energy', 'power', 'generation', 'output', 'yield', 'dc_power', 'ac_power'])]
        
        for col in energy_cols:
            # Skip if column doesn't exist or has all NaN values
            if col not in self.processed_data.columns or self.processed_data[col].isna().all():
                continue
                
            print(f"Creating features for {col}")
            
            # Rolling statistics
            if len(self.processed_data) > 4:
                self.processed_data[f'{col}_rolling_mean_4'] = self.processed_data[col].rolling(4).mean()
                self.processed_data[f'{col}_rolling_std_4'] = self.processed_data[col].rolling(4).std()
            
            if len(self.processed_data) > 24:
                self.processed_data[f'{col}_rolling_mean_24'] = self.processed_data[col].rolling(24).mean()
                self.processed_data[f'{col}_rolling_max_24'] = self.processed_data[col].rolling(24).max()
            
            # Percentage change
            self.processed_data[f'{col}_pct_change'] = self.processed_data[col].pct_change()
            
            # Lag features
            if len(self.processed_data) > 1:
                self.processed_data[f'{col}_lag_1'] = self.processed_data[col].shift(1)
            
            if len(self.processed_data) > 24:
                self.processed_data[f'{col}_lag_24'] = self.processed_data[col].shift(24)
        
        # If we have plant_id or source_key, create aggregated features
        if 'plant_id' in self.processed_data.columns:
            print("Creating plant-level aggregations")
            plant_means = self.processed_data.groupby('plant_id')[energy_cols].transform('mean')
            for col in energy_cols:
                self.processed_data[f'{col}_plant_mean_ratio'] = self.processed_data[col] / plant_means[col]
        
        if 'source_key' in self.processed_data.columns:
            print("Creating source-level aggregations")
            source_means = self.processed_data.groupby('source_key')[energy_cols].transform('mean')
            for col in energy_cols:
                self.processed_data[f'{col}_source_mean_ratio'] = self.processed_data[col] / source_means[col]
        
        print(f"Created {len(self.processed_data.columns) - len(self.cleaned_data.columns)} new features")
        return self
    
    def save_output(self):
        """Step 4: Save processed data"""
        import os
        
        print("Saving output...")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(self.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        
        # Save the processed data
        self.processed_data.to_csv(self.output_file, index=False)
        print(f"Output saved to {self.output_file}")
        return self
    
    def run_pipeline(self):
        """Run the complete pipeline"""
        self.load_data().clean_data().create_features().save_output()
        print("Pipeline completed successfully!")
        return self.processed_data

# Run the pipeline
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Energy Data Pipeline')
    parser.add_argument('--input', type=str, help='Input file path')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    # Create pipeline with provided or default values
    pipeline = EnergyDataPipeline(
        input_file=args.input,
        output_file=args.output
    )
    
    # Run the complete pipeline
    result = pipeline.run_pipeline()
    
    # Display results
    print("\nFinal dataset shape:", result.shape)
    print("\nSample of processed data:")
    print(result.head())
    
    # Display column information
    print("\nColumns in processed dataset:")
    for col in result.columns:
        print(f"- {col}")
        
    print(f"\nOutput saved to: {pipeline.output_file}")