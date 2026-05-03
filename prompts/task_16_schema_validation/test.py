import pandas as pd
import os
import sys
from io import StringIO
import subprocess

def test():
    # Test 1: Check if script runs successfully with valid data
    result = subprocess.run([sys.executable, 'solution.py'], 
                          capture_output=True, text=True)
    
    # Should exit with code 0 and print success message
    assert result.returncode == 0, f"Script should exit with code 0 for valid data, got {result.returncode}"
    assert 'SUCCESS' in result.stdout or 'success' in result.stdout.lower(), \
        f"Should print success message, got: {result.stdout}"
    
    # Check if output file exists
    assert os.path.exists('validated.csv'), "Output file 'validated.csv' not found"
    
    # Read and verify output
    df = pd.read_csv('validated.csv')
    assert len(df) == 3, f"Expected 3 rows, got {len(df)}"
    assert list(df.columns) == ['id', 'name', 'email', 'age', 'city'], \
        f"Columns should match input, got {list(df.columns)}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
