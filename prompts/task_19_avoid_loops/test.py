import pandas as pd
import os
import re

def test():
    # Check if output file exists
    assert os.path.exists('transformed.csv'), "Output file 'transformed.csv' not found"
    
    # Read output
    df = pd.read_csv('transformed.csv')
    
    # Check columns
    expected_columns = ['id', 'name', 'value']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check all values are doubled
    expected_values = {
        1: 200,   # Alice: 100 * 2
        2: 300,   # Bob: 150 * 2
        3: 400,   # Charlie: 200 * 2
        4: 150,   # David: 75 * 2
        5: 600    # Eve: 300 * 2
    }
    
    for id_val, expected in expected_values.items():
        actual = df[df['id'] == id_val]['value'].iloc[0]
        assert actual == expected, f"Expected value {expected} for id {id_val}, got {actual}"
    
    # Check other columns unchanged
    names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
    for name in names:
        assert name in df['name'].values, f"Name {name} should be unchanged"
    
    print("All tests passed!")

def check_solution_code():
    """Check if solution avoids row-wise loops"""
    try:
        with open('solution.py', 'r') as f:
            code = f.read()
        
        # Check for inefficient patterns
        forbidden_patterns = ['iterrows()', 'itertuples()', "apply(.*axis=1"]
        found_forbidden = []
        
        for pattern in forbidden_patterns:
            if re.search(pattern, code):
                found_forbidden.append(pattern)
        
        if found_forbidden:
            print(f" Warning:Solution uses row-wise iteration: {found_forbidden}")
        else:
            print("Solution appears to avoid row-wise loops")
            
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    test()
    check_solution_code()
