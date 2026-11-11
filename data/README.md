# Dataset guide

## Processed files

- `processed/f1_combined_2021_2025_final.csv`: 2,260 driver-race records and 17 columns; the shared input for the final notebook and Flask app.
- `processed/f1_combined_2021_2025_cleaned.csv`: an earlier cleaned/combined dataset retained for the preparation history.

The final file contains driver and constructor identifiers, engine manufacturer, Grand Prix, circuit turns and length, date, qualifying times, finishing position, points and other race-outcome fields. Only the seven features listed in the README are used as model inputs. Outcome fields such as points and finishing position are not supplied as prediction inputs.

Dates in the file span 2021–2025. Coverage, duplicate records and missingness should be checked before interpreting season-level totals. A row is a driver-race entry, not an entire race.

## Raw source tables

`raw/` contains the supplied constructor standings, driver standings, qualifying results, race results and race calendar tables. They provide context for the original preparation process. The repository does not claim to include a complete automated reconstruction of the final merged file from these tables.

The domain report refers to F1DB and public motorsport datasets. Historical scripts under `scripts/experiments/` show attempted collection from GP Racing Stats and Ergast. They are archival evidence and were not rerun during packaging. The supplied files do not establish a complete row-by-row source history or a project-wide data license.
