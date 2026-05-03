import pandas as pd
import os
import numpy as np

def test():
    # Check if output file exists
    assert os.path.exists('clean_data.csv'), "Output file 'clean_data.csv' not found"
    
    # Read output
    df = pd.read_csv('clean_data.csv')
    
    # Check no nulls remain
    assert not df.isnull().any().any(), "There are still null values in the output"
    
    # Check number of rows (2 rows with nulls removed)
    assert len(df) == 3, f"Expected 3 rows (5 - 2 null rows), got {len(df)}"
    
    # Check age is integer type
    assert df['age'].dtype in ['int64', 'int32'], f"Age should be integer, got {df['age'].dtype}"
    
    # Check salary is float type
    assert df['salary'].dtype in ['float64', 'float32'], f"Salary should be float, got {df['salary'].dtype}"
    
    # Check names are trimmed (no leading/trailing spaces)
    for name in df['name']:
        assert name == name.strip(), f"Name '{name}' has leading/trailing spaces"
    
    # Check specific values are present
    names = df['name'].tolist()
    assert 'Alice' in names, "Alice should be in output"
    assert 'David' in names, "David should be in output"
    assert 'Eve' in names, "Eve should be in output"
    
    # Check Bob and Charlie are NOT in output (had nulls)
    assert 'Bob' not in names, "Bob should not be in output (had null age)"
    assert 'Charlie' not in names, "Charlie should not be in output (had null salary)"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
