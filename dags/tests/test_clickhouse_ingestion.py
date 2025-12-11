from pathlib import Path

import pandas as pd
from src.clickhouse_ingestion import ClickHouseIngestion


def test_load_csv_files_to_clickhouse(test_clickhouse_interface):
    """
    Test loading CSV files into ClickHouse.
    """
    ch_ingestion = ClickHouseIngestion()
    ch_ingestion.load_csv_files_to_clickhouse()

    # query ClickHouse to verify data was inserted
    inputs_folder = Path(__file__).parent.parent / "input"
    csv_files = list(inputs_folder.glob("*.csv"))

    for csv_file in csv_files:
        table_name = csv_file.stem
        df = pd.read_csv(csv_file)

        # Query ClickHouse for row count
        result = test_clickhouse_interface.execute_query(
            f"SELECT COUNT(*) FROM {table_name}"
        )
        clickhouse_count = result.result_rows[0][0]

        assert (
            clickhouse_count == len(df)
        ), f"Row count mismatch for table {table_name}: expected {len(df)}, got {clickhouse_count}"
        print(
            f"Test passed for table '{table_name}': {clickhouse_count} rows inserted successfully."
        )
