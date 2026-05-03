import pandas as pd
import os
import re

def test():
    # Check if output file exists
    assert os.path.exists('filtered.csv'), "Output file 'filtered.csv' not found"
    
    # Read output
    df = pd.read_csv('filtered.csv')
    
    # Check columns
    expected_columns = ['id', 'value', 'category']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check only rows with value > 1000 are present
    assert (df['value'] > 1000).all(), "All values should be > 1000"
    
    # Check correct rows are filtered (ids: 2,4,5,7,8,10)
    expected_ids = {2, 4, 5, 7, 8, 10}
    actual_ids = set(df['id'].tolist())
    assert actual_ids == expected_ids, f"Expected ids {expected_ids}, got {actual_ids}"
    
    # Check number of rows
    assert len(df) == 6, f"Expected 6 rows (value > 1000), got {len(df)}"
    
    print("✅ All tests passed!")

def check_solution_code():
    """Check if solution uses efficient methods"""
    try:
        with open('solution.py', 'r') as f:
            code = f.read()
        
        # Check for inefficient patterns
        if 'iterrows()' in code or 'itertuples()' in code:
            print("⚠️ Warning: Solution uses row-wise iteration (inefficient)")
        
        if 'read_csv' in code and code.count('read_csv') > 1:
            print("⚠️ Warning: Solution may load data multiple times")
        
        # Check for efficient patterns
        if 'df[' in code and '>' in code:
            print("✅ Solution appears to use vectorized filtering")
        elif '.query(' in code:
            print("✅ Solution uses query method")
            
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    test()
    check_solution_code()
