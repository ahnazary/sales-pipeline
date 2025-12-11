from pytest import fixture
from src.clickhouse_interface import ClickHouseInterface


@fixture
def test_clickhouse_interface():
    """
    Test ClickHouseInterface functionality.
    """
    ch_interface = ClickHouseInterface(
        host="localhost", port=8123, username="admin", password="admin"
    )

    yield ch_interface

    # delete all tables created during tests
    result = ch_interface.execute_query("SHOW TABLES")
    tables = [row[0] for row in result.result_rows]
    for table in tables:
        ch_interface.execute_query(f"DROP TABLE IF EXISTS {table}")
