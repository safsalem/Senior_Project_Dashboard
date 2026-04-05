from pathlib import Path
import pandas as pd
import pytest
from ai_model.data import load_and_combine_data

def test_load_and_combine_data():
    # Assuming the CSV files are in the specified directory
    data_dir = Path("co_and_nox_emission_data_set")
    combined_data = load_and_combine_data(data_dir)

    # Check if the combined DataFrame is not empty
    assert not combined_data.empty, "Combined DataFrame is empty"

    # Check if the expected columns are present
    expected_columns = ["NOX", "AT", "TIT", "TAT", "_source_file"]
    for col in expected_columns:
        assert col in combined_data.columns, f"Column {col} is missing from the combined DataFrame"

    # Check if the number of rows is as expected (this can be adjusted based on your dataset)
    expected_row_count = sum(1 for _ in data_dir.glob("*.csv")) * 100  # Example: assuming each CSV has ~100 rows
    assert combined_data.shape[0] >= expected_row_count, "Combined DataFrame has fewer rows than expected"