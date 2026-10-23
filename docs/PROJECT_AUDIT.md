# Publication audit — 22 October 2026

All original files were inspected in place. Sizes use MiB (1,048,576 bytes); directory totals include their descendant files. No original data or PBIX file was changed, moved, or deleted.

## Original inventory and GitHub recommendation

| File / folder | Size | Purpose | Recommendation |
| --- | ---: | --- | --- |
| `data_raw/` | 155.86 MiB | Original TLC downloads | Exclude; document source |
| `data_raw/yellow_tripdata_2024-01.parquet` | 47.65 MiB | January raw trips | Exclude; public download |
| `data_raw/yellow_tripdata_2024-07.parquet` | 49.88 MiB | July raw trips | Exclude; public download |
| `data_raw/yellow_tripdata_2024-09.parquet` | 58.34 MiB | September raw trips | Exclude; public download |
| `data_ref/` | 0.012 MiB | Reference lookup | Include normally |
| `data_ref/taxi_zone_lookup.csv` | 0.012 MiB | TLC zone ID to borough/zone | Include normally |
| `outputs/` | 2,174.94 MiB | Generated outputs | Mixed, itemized below |
| `outputs/data_quality_report.txt` | 0.001 MiB | Processing counts and sample summary | Include normally |
| `outputs/yellow_agg_daily.csv` | 1.053 MiB | Date/hour/payment aggregate | Include normally |
| `outputs/yellow_agg_daily_borough.csv` | 0.233 MiB | Date/borough/payment aggregate | Include normally |
| `outputs/yellow_clean_sample.csv` | 108.483 MiB | One million cleaned rows | Exclude; include 1,000-row sample |
| `outputs/yellow_tripdata_2024_combined_cleaned.csv` | 1,032.582 MiB | Full combined cleaned trips | Exclude; regenerable by optional script |
| `outputs/yellow_tripdata_2024-01_cleaned.csv` | 317.921 MiB | January cleaned trips | Exclude; generation script missing |
| `outputs/yellow_tripdata_2024-07_cleaned.csv` | 329.351 MiB | July cleaned trips | Exclude; generation script missing |
| `outputs/yellow_tripdata_2024-09_cleaned.csv` | 385.310 MiB | September cleaned trips | Exclude; generation script missing |
| `scripts/` | 0.013 MiB | Python source | Include normally |
| `scripts/convert_parquet_to_csv.py` | 0.003 MiB | Optional streamed-batch combined CSV | Include normally |
| `scripts/process_taxi_data.py` | 0.010 MiB | Quality, sample, and aggregates | Include normally |
| `Taxi_Dashboard.pbix` | 196.317 MiB | Power BI report and data model | Include through Git LFS after review |

**Original total:** 2,649,894,667 bytes = **2,527.14 MiB / 2.468 GiB**. There was no original README, screenshot, or other visualization file outside the PBIX. No Git repository existed at audit time. The current layout keeps original paths because both scripts assume execution from the project root.

## Processing and dependencies

| Script | Inputs | Implemented transformations | Outputs | Caveat |
| --- | --- | --- | --- | --- |
| `process_taxi_data.py` | Three explicitly named monthly Parquet files; optional taxi zone lookup | Reads nine source fields; lowercase names; remove missing dates; derive pickup month/date/hour/day-of-week and trip duration; filter invalid duration/distance/total; cap distance/duration/total; left join pickup borough; aggregate sums then weighted averages; randomized sample with seed 42; quality counts | `yellow_agg_daily.csv`, `yellow_agg_daily_borough.csv`, `yellow_clean_sample.csv`, `data_quality_report.txt` | Loads each full monthly selected-field table into memory; overwrites outputs |
| `convert_parquet_to_csv.py` | Every `*.parquet` file in `data_raw/` | Iterates batches of 100,000 rows; lowercase names; derive duration; filter invalid duration/distance/total; cap same fields | `yellow_tripdata_2024_combined_cleaned.csv` | Deletes existing combined output before running; catches per-file exceptions, so partial output is possible |

The scripts are independent, not sequential dependencies. The three per-month cleaned CSVs have no generating code in this folder. The PBIX layout references the two aggregate table names, but the exact Power Query sources and refresh paths are unverified. Required Python packages are `pandas`, `numpy`, and `pyarrow`; the standard library supplies the other imports.

## Safe PBIX inspection

The PBIX is a readable ZIP container. `Report/Layout` was parsed as UTF-16LE JSON without editing the file. It contains **one page** (`Page 1`) and **14 visual containers**: four KPI cards, two line charts, one matrix, one donut chart, two bar charts, three text boxes, and one image. The six non-card data visuals cover daily trips, daily revenue, day-of-week/hour trips, payment share, tips by payment label, and revenue by pickup borough. No slicer is present in the layout. The report references two aggregate tables and nine distinct measure names: `Total Trips`, `Total Revenue`, `Avg Fare`, `Avg Duration`, `Total Tips`, `Borough Revenue`, `Borough Trips`, `Borough Avg Distance`, and `Borough Avg Duration`.

The proprietary `DataModel` entry is approximately 205.8 MB and was left untouched. The report layout does not reveal measure DAX definitions, complete model tables, relationships, Power Query steps, refresh settings, or current card values. The included DAX query-view file contains an editor query, not a complete verified measure inventory. Those items require Power BI Desktop or a supported semantic-model export. The report contains a visible personal identifier in a text box; review and remove it in Desktop before any public PBIX or screenshot upload. The original PBIX SHA-256 at audit time was `e889a0fef84556e8d8a6a5c2be4f39428f69acd01a4595bad96e837741bb6068`.

## Verified metrics

| Metric | Verified value | Evidence | Confidence / limitation |
| --- | ---: | --- | --- |
| Raw rows | 9,674,557 | Sum of three Parquet metadata row counts | Exact for local files |
| Rows dropped | 319,690 | Existing quality report; raw minus cleaned output | Exact aggregate difference; specific filters from script |
| Cleaned rows | 9,354,867 | Quality report, combined CSV line count, both aggregate `trip_count` sums | Exact for present outputs |
| One-million-row sample | 1,000,000 rows | CSV line count | Exact for present output |
| Daily aggregate | 11,072 rows | CSV line count | Exact |
| Borough aggregate | 2,533 rows | CSV line count | Exact |
| Source dataset size | 155.86 MiB | Local Parquet file sizes | Exact local size |
| Report pages | 1 | PBIX `Report/Layout` sections | Exact for saved layout |
| KPI cards | 4 | PBIX visual types | Exact for saved layout |
| Distinct referenced measures | 9 | PBIX visual query references | Lower bound for full model inventory |
| Data visuals | 10, including cards | PBIX visual types | Exact for saved layout; 14 containers total |
| Source months | Jan, Jul, Sep 2024 | Filenames and script `FILES` | Exact intended selection |
| Observed pickup-date range | 2002-12-31 to 2024-10-01 | Aggregate `pickup_date` extrema | Exact for present aggregates; includes anomalies |
| Trips with pickup date outside selected 2024 months | 112 | Sum of daily aggregate `trip_count` after date check | Exact for present aggregate |
| Reconstructed total amount | $267,501,699.33 | Sum of `trip_count × avg_total_amount` in daily aggregate | CSV-derived; Power BI DAX unverified |
| Reconstructed average fare | $19.77 | Trip-weighted daily `avg_fare_amount` | CSV-derived; Power BI DAX unverified |
| Reconstructed average duration | 16.86 minutes | Trip-weighted daily `avg_trip_duration` | CSV-derived; Power BI DAX unverified |
| Processing duration | Not measured | No duration log or timestamped benchmark | Unavailable |

## Large-file and compression assessment

GitHub blocks ordinary Git files above 100 MiB and warns above 50 MiB. The PBIX and five large CSVs exceed 100 MiB. The September Parquet is under 100 MiB but above the 50 MiB warning threshold. ZIP or another archive does not bypass the file-size rule. A zlib level-6 test on the **first 8 MiB** of three CSVs yielded approximately 0.199× for combined/January cleaned data and 0.258× for the one-million-row sample. These are local segment ratios, not full-archive sizes or promises; the combined CSV could still be over 100 MiB compressed. Compression saves bytes but adds redundant artifacts and makes review harder. Excluding regenerated trip-level outputs and linking the public Parquet sources is the practical choice. The 1,000-row sample is 113,219 bytes and preserves its 16-column schema.

Git LFS 3.2.0 is installed. `.gitattributes` assigns `*.pbix` to LFS. **No repository was initialized, no file was staged, and no upload or account quota check was possible** without a Git repository and GitHub account/repository context. The proposed initial Git content is roughly **207.4 MB transferred**: approximately 205.9 MB as a PBIX LFS object and 1.5 MB of ordinary files; Git metadata and future screenshots may add to this. Actual GitHub LFS storage and bandwidth depend on the destination account's plan and current usage. Review the account's [Git LFS billing page](https://docs.github.com/en/billing/concepts/product-billing/git-lfs) before upload. GitHub's [large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) describes the normal Git limits.

## Publication checks and blockers

- Keep existing paths. The current scripts and outputs are designed around them; no substantial restructuring was performed.
- Remove the personal identifier from a **publication copy** of the PBIX in Desktop, inspect all pages/model contents for other sensitive details, and save without overwriting the original unless desired.
- Check Power Query source paths, refresh requirements, DAX measures, model tables, and relationships in Desktop. The saved layout alone cannot verify them.
- Capture the genuine one-page screenshot using `assets/screenshots/README.md`; no image was fabricated or linked as if it existed.
- Reproduce the three per-month cleaned CSVs only if their missing generation code is recovered; they are excluded from Git.
- Initialize Git only after PBIX review. Before committing, run `git check-attr filter -- Taxi_Dashboard.pbix` (expected `lfs`), then `git add --dry-run .` and inspect the included paths. The PBIX should remain on LFS. No commit or push has been made.

## Screenshot follow-up

During screenshot preparation on 22 October 2026, `Taxi_Dashboard.pbix` changed outside this agent's file operations while Power BI Desktop was in use. Its current SHA-256 is `710494e07c662db4f677bf4f4eb655b1fd4bf26a1d02b3d60f2ac563b9c1f781`, and its ZIP container passes integrity checking. The report definition now uses individual JSON files rather than `Report/Layout`; the formerly identifying text box is blank. This does not establish that all visible or model content is publication-safe. No dashboard screenshots were present at this check. The agent did not save or overwrite the PBIX.
