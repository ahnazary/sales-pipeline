"""
Module to interface with ClickHouse database.
It can be used if the docker-compose setup is used (Since that spins up a ClickHouse instance).
"""

import clickhouse_connect


class ClickHouseInterface:
    def __init__(self, host="localhost", port=8123, username="admin", password="admin"):
        self.client = clickhouse_connect.get_client(
            host=host, port=port, username=username, password=password
        )

    def execute_query(self, query: str):
        return self.client.query(query)

    def insert_data(self, table: str, df):
        """
        Insert DataFrame data into ClickHouse table.
        Preprocesses data to handle date/datetime conversions.

        :param table: name of the table to insert into
        :param df: pandas DataFrame to insert
        """
        # Create a copy to avoid modifying original DataFrame
        df_copy = df.copy()

        # Convert date objects to strings for ClickHouse compatibility
        for col_name in df_copy.columns:
            col_data = df_copy[col_name]

            # Check if column contains date objects
            if col_data.dtype == "object" and len(col_data) > 0:
                # Check if first non-null value is a date
                first_value = (
                    col_data.dropna().iloc[0] if len(col_data.dropna()) > 0 else None
                )
                if first_value is not None and hasattr(first_value, "strftime"):
                    # Convert date objects to string format
                    df_copy[col_name] = col_data.astype(str)

        self.create_table_if_not_exists(df_copy, table)
        self.client.insert_df(table, df_copy)

    def create_table_if_not_exists(self, df, table: str):
        """
        Create a ClickHouse table based on DataFrame schema if it doesn't exist.

        :param df: pandas DataFrame to infer schema from
        :param table: name of the table to create
        """
        # Map pandas dtypes to ClickHouse types
        dtype_mapping = {
            "object": "String",
            "int64": "Int64",
            "int32": "Int32",
            "float64": "Float64",
            "float32": "Float32",
            "bool": "UInt8",
            "datetime64[ns]": "DateTime",
            "datetime64[ns, UTC]": "DateTime",
        }

        # Build column definitions
        columns = []
        for col_name, dtype in df.dtypes.items():
            dtype_str = str(dtype)

            # Handle datetime types
            if "datetime64" in dtype_str:
                clickhouse_type = "DateTime"
            # Handle object types - could be strings or dates
            elif dtype_str == "object":
                # Check if this column contains date objects
                col_data = df[col_name].dropna()
                if len(col_data) > 0:
                    first_value = col_data.iloc[0]
                    if hasattr(first_value, "strftime"):  # It's a date/datetime object
                        clickhouse_type = "Date"
                    else:
                        clickhouse_type = "Nullable(String)"
                else:
                    clickhouse_type = "Nullable(String)"
            else:
                clickhouse_type = dtype_mapping.get(dtype_str, "String")

            columns.append(f"`{col_name}` {clickhouse_type}")

        # Create table query
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            {', '.join(columns)}
        ) ENGINE = MergeTree()
        ORDER BY tuple()
        """

        # Execute the query
        self.client.command(create_query)
