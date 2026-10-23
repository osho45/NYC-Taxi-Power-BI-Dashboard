import pandas as pd
import pyarrow.dataset as ds
import pyarrow as pa
import os
import numpy as np

# Constants
DATA_RAW_DIR = 'data_raw'
DATA_REF_DIR = 'data_ref'
OUTPUT_DIR = 'outputs'
FILES = [
    'yellow_tripdata_2024-01.parquet',
    'yellow_tripdata_2024-07.parquet',
    'yellow_tripdata_2024-09.parquet'
]
LOOKUP_FILE = 'taxi_zone_lookup.csv'
REPORT_FILE = 'data_quality_report.txt'
RANDOM_SEED = 42
TARGET_SAMPLE_SIZE = 1_000_000

# Columns required for processing
REQUIRED_COLUMNS = [
    'tpep_pickup_datetime',
    'tpep_dropoff_datetime',
    'trip_distance',
    'total_amount',
    'fare_amount',
    'tip_amount',
    'payment_type',
    'PULocationID', 
    'DOLocationID'
]

def load_lookup_data():
    path = os.path.join(DATA_REF_DIR, LOOKUP_FILE)
    if not os.path.exists(path):
        print(f"Warning: {path} not found. Borough information will be missing.")
        return None
    print(f"Loading lookup from {path}...")
    df = pd.read_csv(path)
    df['LocationID'] = df['LocationID'].astype(int)
    return df

def load_and_process_chunk(file_path, lookup_df):
    """
    Loads a single parquet file, cleans, filters, merges,
    and returns (daily_agg, borough_agg, sample_df, stats).
    """
    print(f"Processing {file_path}...")
    
    stats = {
        'total_rows_raw': 0,
        'missing_values': {},
        'rows_dropped_missing_dates': 0,
        'rows_dropped_invalid': 0,
        'rows_after_cleaning': 0
    }

    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return None, None, None, stats

    try:
        dataset = ds.dataset(file_path, format="parquet")
        table = dataset.to_table(columns=REQUIRED_COLUMNS)
        df = table.to_pandas()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None, None, None, stats

    stats['total_rows_raw'] = len(df)

    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()
    
    col_map = {
        'tpep_pickup_datetime': 'pickup_datetime',
        'tpep_dropoff_datetime': 'dropoff_datetime',
        'pulocationid': 'pulocationid',
        'dolocationid': 'dolocationid'
    }
    df = df.rename(columns=col_map)
    
    # Track missing values before cleaning
    # We check columns that exist in df
    for col in df.columns:
        stats['missing_values'][col] = df[col].isnull().sum()

    # Feature Engineering (needed for filter check)
    # Check if we have datetime cols
    if 'pickup_datetime' in df.columns and 'dropoff_datetime' in df.columns:
         # Missing Dates Filter
        initial_len = len(df)
        df = df.dropna(subset=['pickup_datetime', 'dropoff_datetime'])
        stats['rows_dropped_missing_dates'] = initial_len - len(df)
        
        df['month'] = df['pickup_datetime'].dt.month
        df['pickup_date'] = df['pickup_datetime'].dt.date
        df['pickup_hour'] = df['pickup_datetime'].dt.hour
        df['pickup_dow'] = df['pickup_datetime'].dt.dayofweek
        
        # Duration in minutes
        df['trip_duration_min'] = (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds() / 60.0
        
        # Filtering Invalid/Outliers
        # Missing or invalid checks
        mask_valid = (
            (df['trip_duration_min'] > 0) & 
            (df['trip_distance'] > 0) & 
            (df['total_amount'] >= 0)
        )
        
        len_before_filter = len(df)
        df = df[mask_valid].copy()
        stats['rows_dropped_invalid'] = len_before_filter - len(df)
        
        # Cap extreme outliers (in-place, doesn't drop rows)
        df['trip_distance'] = np.clip(df['trip_distance'], None, 100)
        df['trip_duration_min'] = np.clip(df['trip_duration_min'], None, 300)
        df['total_amount'] = np.clip(df['total_amount'], None, 1000)

    else:
        # If key columns missing completely
        stats['rows_dropped_missing_dates'] = len(df)
        df = pd.DataFrame() # Empty

    # --- Merge with Lookup ---
    if not df.empty and lookup_df is not None:
        df = df.merge(lookup_df[['LocationID', 'Borough']], left_on='pulocationid', right_on='LocationID', how='left')
        df.rename(columns={'Borough': 'pickup_borough'}, inplace=True)
        df.drop(columns=['LocationID'], inplace=True)
    elif not df.empty:
        df['pickup_borough'] = 'Unknown'
        
    if not df.empty:
        df['pickup_borough'] = df['pickup_borough'].fillna('Unknown')

    stats['rows_after_cleaning'] = len(df)

    if df.empty:
        return None, None, None, stats

    # --- Aggregations (Intermediate) ---
    df['trip_count'] = 1
    
    daily_group_cols = ['month', 'pickup_date', 'pickup_hour', 'pickup_dow', 'payment_type']
    daily_agg_funcs = {
        'trip_count': 'sum',
        'total_amount': 'sum',
        'fare_amount': 'sum',
        'tip_amount': 'sum',
        'trip_distance': 'sum',
        'trip_duration_min': 'sum'
    }
    daily_chunk_agg = df.groupby(daily_group_cols, as_index=False).agg(daily_agg_funcs)

    borough_group_cols = ['month', 'pickup_date', 'pickup_borough', 'payment_type']
    borough_chunk_agg = df.groupby(borough_group_cols, as_index=False).agg(daily_agg_funcs)
    
    # --- Sampling (Intermediate) ---
    rows_to_sample = 400_000
    if len(df) > rows_to_sample:
        chunk_sample = df.sample(n=rows_to_sample, random_state=RANDOM_SEED)
    else:
        chunk_sample = df
        
    return daily_chunk_agg, borough_chunk_agg, chunk_sample, stats

def finalize_aggregation(agg_list, group_cols, output_name):
    # print(f"Finalizing aggregation {output_name}...")
    global_agg = pd.concat(agg_list, ignore_index=True)
    final_sums = global_agg.groupby(group_cols, as_index=False).sum()
    
    final_output = pd.DataFrame()
    final_output[group_cols] = final_sums[group_cols]
    final_output['trip_count'] = final_sums['trip_count']
    final_output['avg_fare_amount'] = final_sums['fare_amount'] / final_sums['trip_count']
    final_output['avg_total_amount'] = final_sums['total_amount'] / final_sums['trip_count']
    final_output['total_tip_amount'] = final_sums['tip_amount']
    final_output['avg_trip_distance'] = final_sums['trip_distance'] / final_sums['trip_count']
    final_output['avg_trip_duration'] = final_sums['trip_duration_min'] / final_sums['trip_count']
    
    out_path = os.path.join(OUTPUT_DIR, output_name)
    final_output.to_csv(out_path, index=False)
    # print(f"Saved {output_name} to {out_path}")

def generate_report(global_stats, final_sample):
    print("Generating data quality report...")
    
    lines = []
    lines.append("DATA QUALITY REPORT")
    lines.append("===================")
    lines.append(f"Total Raw Rows: {global_stats['total_rows_raw']:,}")
    lines.append("-" * 20)
    lines.append(f"Rows Dropped (Missing Dates): {global_stats['rows_dropped_missing_dates']:,}")
    lines.append(f"Rows Dropped (Invalid/Filters): {global_stats['rows_dropped_invalid']:,}")
    lines.append(f"Total Rows Dropped: {global_stats['rows_dropped_missing_dates'] + global_stats['rows_dropped_invalid']:,}")
    lines.append(f"Final Clean Rows (Approx): {global_stats['rows_after_cleaning']:,}")
    lines.append("-" * 20)
    lines.append("Missing Values (Raw Data):")
    for col, count in global_stats['missing_values'].items():
        pct = (count / global_stats['total_rows_raw']) * 100 if global_stats['total_rows_raw'] > 0 else 0
        lines.append(f"  {col}: {count:,} ({pct:.2f}%)")
        
    lines.append("-" * 20)
    lines.append("Statistical Summary (Based on 1M Cleaned Sample):")
    
    stats_cols = ['trip_distance', 'trip_duration_min', 'total_amount']
    
    if not final_sample.empty:
        desc = final_sample[stats_cols].describe(percentiles=[0.5]).T
        # desc has count, mean, std, min, 50%, max
        for col in stats_cols:
            lines.append(f"\n  Column: {col}")
            lines.append(f"    Min: {desc.loc[col, 'min']:.2f}")
            lines.append(f"    Median: {desc.loc[col, '50%']:.2f}")
            lines.append(f"    Max: {desc.loc[col, 'max']:.2f}")
    else:
        lines.append("\n  (No sample data available for stats)")

    report_content = "\n".join(lines)
    print(report_content)
    
    with open(os.path.join(OUTPUT_DIR, REPORT_FILE), 'w') as f:
        f.write(report_content)
    print(f"Report saved to {os.path.join(OUTPUT_DIR, REPORT_FILE)}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    lookup_df = load_lookup_data()
    
    all_daily_aggs = []
    all_borough_aggs = []
    all_samples = []
    
    global_stats = {
        'total_rows_raw': 0,
        'missing_values': {},
        'rows_dropped_missing_dates': 0,
        'rows_dropped_invalid': 0,
        'rows_after_cleaning': 0
    }
    
    for filename in FILES:
        path = os.path.join(DATA_RAW_DIR, filename)
        daily_agg, borough_agg, sample, stats = load_and_process_chunk(path, lookup_df)
        
        # Accumulate stats
        global_stats['total_rows_raw'] += stats['total_rows_raw']
        global_stats['rows_dropped_missing_dates'] += stats['rows_dropped_missing_dates']
        global_stats['rows_dropped_invalid'] += stats['rows_dropped_invalid']
        global_stats['rows_after_cleaning'] += stats['rows_after_cleaning']
        
        for col, count in stats['missing_values'].items():
            global_stats['missing_values'][col] = global_stats['missing_values'].get(col, 0) + count

        if daily_agg is not None:
            all_daily_aggs.append(daily_agg)
            all_borough_aggs.append(borough_agg)
            all_samples.append(sample)
    
    if not all_daily_aggs:
        print("No data processed.")
        return

    # Finalize Aggregations
    finalize_aggregation(all_daily_aggs, ['month', 'pickup_date', 'pickup_hour', 'pickup_dow', 'payment_type'], 'yellow_agg_daily.csv')
    finalize_aggregation(all_borough_aggs, ['month', 'pickup_date', 'pickup_borough', 'payment_type'], 'yellow_agg_daily_borough.csv')

    # Finalize Sample
    print("Finalizing sample...")
    global_sample = pd.concat(all_samples, ignore_index=True)
    if len(global_sample) > TARGET_SAMPLE_SIZE:
        final_sample = global_sample.sample(n=TARGET_SAMPLE_SIZE, random_state=RANDOM_SEED)
    else:
        final_sample = global_sample
    final_sample.to_csv(os.path.join(OUTPUT_DIR, 'yellow_clean_sample.csv'), index=False)
    
    # Generate Report
    generate_report(global_stats, final_sample)

if __name__ == "__main__":
    main()
