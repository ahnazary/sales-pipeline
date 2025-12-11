"""
Script to load CSV files from inputs folder into ClickHouse database.
Each CSV file is loaded into a separate table with the same name and schema.
"""

from pathlib import Path

import pandas as pd
from src.clickhouse_interface import ClickHouseInterface


class ClickHouseIngestion:
    def __init__(self, ch_interface=None):
        self.ch_interface = ch_interface or ClickHouseInterface(
            host="localhost", port=8123, username="admin", password="admin"
        )
        self.inputs_folder = Path(__file__).parent.parent.parent / "input"

    def load_csv_files_to_clickhouse(self):
        """
        Load all CSV files from inputs folder into ClickHouse.
        Creates tables automatically if they don't exist.
        """
        # Initialize ClickHouse interface
        ch_interface = ClickHouseInterface(
            host="localhost", port=8123, username="admin", password="admin"
        )
        # Get all CSV files in inputs folder
        csv_files = list(self.inputs_folder.glob("*.csv"))

        print(f"Found {len(csv_files)} CSV files to process")

        # Process each CSV file
        for csv_file in csv_files:
            try:
                # Get table name from filename (without .csv extension)
                table_name = csv_file.stem

                print(f"\nProcessing {csv_file.name}...")

                # Read CSV file into DataFrame
                df = pd.read_csv(csv_file)

                print(f"  Loaded {len(df)} rows from {csv_file.name}")

                # Insert data into ClickHouse (creates table if not exists)
                ch_interface.insert_data(table_name, df)

                print(f"  ✓ Successfully inserted data into table '{table_name}'")

            except Exception as e:
                print(f"  ✗ Error processing {csv_file.name}: {str(e)}")
                continue


if __name__ == "__main__":
    ingestion = ClickHouseIngestion()
    ingestion.load_csv_files_to_clickhouse()
