import pandas as pd
import os
import numpy as np

def test():
    assert os.path.exists('cleaned.csv'), "Output file 'cleaned.csv' not found"
    
    df = pd.read_csv('cleaned.csv')
    
    assert len(df) == 5, f"Expected 5 rows (1 removed due to empty city), got {len(df)}"
    
    # Check ages are filled
    ages = df['age'].tolist()
    assert 25.0 in ages, "Age 25 should be present"
    assert 30.0 in ages, "Age 30 should be present"
    assert 35.0 in ages, "Age 35 should be present"
    
    # Check null-like values are replaced
    for val in df['age']:
        assert str(val) not in ['N/A', 'null', 'NULL', '-'], f"Null-like value '{val}' should be replaced"
    
    # Check Diana is removed (empty city)
    assert 'Diana' not in df['name'].values, "Diana should be removed (empty city)"
    
    # Check all valid names are present
    assert 'Alice' in df['name'].values
    assert 'Bob' in df['name'].values
    assert 'Charlie' in df['name'].values
    assert 'Eve' in df['name'].values
    assert 'Frank' in df['name'].values
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
