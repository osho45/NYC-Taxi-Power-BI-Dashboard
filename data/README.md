# Data included in this repository

`samples/yellow_clean_sample_1000.csv` contains 1,000 existing rows selected from the project's already randomized, cleaned sample. It keeps the original 16-column schema; no records were fabricated. The source NYC TLC trip records have no passenger names or contact details in these fields.

The full January, July, and September 2024 Yellow Taxi Parquet files are excluded from Git. Download them from the [NYC TLC trip record page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) to `data_raw/`, retaining their original filenames. The small taxi zone lookup is included at `data_ref/taxi_zone_lookup.csv` and is also available from that page.

The large trip-level CSV outputs remain local and are excluded from Git. The two small aggregates and the quality report in `outputs/` are included because they explain the dashboard's data and allow its results to be checked without rebuilding the full dataset.
