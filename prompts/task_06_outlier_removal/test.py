import pandas as pd
import numpy as np
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Read input to calculate expected
    input_df = pd.read_csv('input.csv')
    mean_val = input_df['value'].mean()
    std_val = input_df['value'].std()
    
    # Expected: remove values > 3 std from mean
    threshold = 3 * std_val
    expected_kept = input_df[np.abs(input_df['value'] - mean_val) <= threshold]
    
    # Check row count
    assert len(df) == len(expected_kept), f"Expected {len(expected_kept)} rows, got {len(df)}"
    
    # Check no outliers remain
    for val in df['value']:
        assert np.abs(val - mean_val) <= threshold, f"Value {val} is an outlier (> 3 std)"
    
    # Check specific outliers are removed (100 and 105)
    assert 100 not in df['value'].values, "Outlier value 100 should be removed"
    assert 105 not in df['value'].values, "Outlier value 105 should be removed"
    
    # Check normal values are kept
    assert 10 in df['value'].values, "Value 10 should be kept"
    assert 15 in df['value'].values, "Value 15 should be kept"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
