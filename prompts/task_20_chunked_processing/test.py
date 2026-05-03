import pandas as pd
import os
import re

def test():
    # Check if output file exists
    assert os.path.exists('processed.csv'), "Output file 'processed.csv' not found"
    
    # Read output
    df = pd.read_csv('processed.csv')
    
    # Check columns
    expected_columns = ['id', 'value', 'category']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check only rows with value > 500 are present
    assert (df['value'] > 500).all(), "All values should be > 500"
    
    # Check correct rows are present (value > 500): 600, 800, 900, 700, 1000
    expected_ids = {2, 4, 6, 8, 10}
    actual_ids = set(df['id'].tolist())
    assert actual_ids == expected_ids, f"Expected ids {expected_ids}, got {actual_ids}"
    
    # Check number of rows
    assert len(df) == 5, f"Expected 5 rows (value > 500), got {len(df)}"
    
    print("✅ All tests passed!")

def check_solution_code():
    """Check if solution uses chunked processing"""
    try:
        with open('solution.py', 'r') as f:
            code = f.read()
        
        # Check for chunked processing patterns
        if 'chunksize' in code:
            print("✅ Solution uses chunksize parameter")
        else:
            print("⚠️ Warning: Solution may not use chunked processing")
        
        if 'for' in code and 'chunk' in code.lower():
            print("✅ Solution iterates over chunks")
        
        if 'concat' in code.lower() or 'append' in code.lower():
            print("✅ Solution combines chunks")
            
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    test()
    check_solution_code()
