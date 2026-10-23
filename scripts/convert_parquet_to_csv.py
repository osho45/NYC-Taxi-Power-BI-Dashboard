import pandas as pd
import os
import glob
import pyarrow.parquet as pq
import numpy as np

# Constants
DATA_RAW_DIR = 'data_raw'
OUTPUT_DIR = 'outputs'
COMBINED_OUTPUT_NAME = 'yellow_tripdata_2024_combined_cleaned.csv'
CHUNK_SIZE = 100_000

def clean_data(df):
    """
    Applies standard cleaning and filtering.
    """
    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()
    
    col_map = {
        'tpep_pickup_datetime': 'pickup_datetime',
        'tpep_dropoff_datetime': 'dropoff_datetime'
    }
    df = df.rename(columns=col_map)
    
    # Ensure datetimes
    if 'pickup_datetime' in df.columns:
        df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
    if 'dropoff_datetime' in df.columns:
        df['dropoff_datetime'] = pd.to_datetime(df['dropoff_datetime'])

    # Feature Engineering
    df['trip_duration_min'] = (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds() / 60.0

    # Filter Invalid Rows
    mask_valid = (
        (df['trip_duration_min'] > 0) & 
        (df['trip_distance'] > 0) & 
        (df['total_amount'] >= 0)
    )
    df = df[mask_valid].copy()
    
    # Cap Outliers
    df['trip_distance'] = np.clip(df['trip_distance'], None, 100)
    df['trip_duration_min'] = np.clip(df['trip_duration_min'], None, 300)
    df['total_amount'] = np.clip(df['total_amount'], None, 1000)
    
    return df

def convert_combine_and_clean(source_dir, output_dir):
    parquet_files = glob.glob(os.path.join(source_dir, '*.parquet'))
    os.makedirs(output_dir, exist_ok=True)
    
    if not parquet_files:
        print(f"No parquet files found in {source_dir}")
        return

    output_path = os.path.join(output_dir, COMBINED_OUTPUT_NAME)
    print(f"Found {len(parquet_files)} parquet files. Merging into {output_path}...")
    
    # Remove existing file if present to start fresh
    if os.path.exists(output_path):
        os.remove(output_path)

    global_first_chunk = True
    total_rows_written = 0

    for file_path in parquet_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        try:
            parquet_file = pq.ParquetFile(file_path)
            
            for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE):
                df = batch.to_pandas()
                df = clean_data(df)
                
                if df.empty:
                    continue
                
                # Write to CSV (Append Mode)
                mode = 'w' if global_first_chunk else 'a'
                header = global_first_chunk
                
                df.to_csv(output_path, index=False, mode=mode, header=header)
                
                total_rows_written += len(df)
                global_first_chunk = False
                
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    print(f"Done. Total rows written: {total_rows_written}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    convert_combine_and_clean(DATA_RAW_DIR, OUTPUT_DIR)
