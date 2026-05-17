import pandas as pd
import os

def test():
    assert os.path.exists('standardized.csv'), "Output file 'standardized.csv' not found"
    
    df = pd.read_csv('standardized.csv')
    
    assert len(df) == 12, f"Expected 12 rows, got {len(df)}"
    
    countries = df['country'].tolist()
    
    # Check standardization
    assert countries.count('United States') == 4, f"Expected 4 'United States', got {countries.count('United States')}"
    assert countries.count('Canada') == 3, f"Expected 3 'Canada', got {countries.count('Canada')}"
    assert countries.count('United Kingdom') == 3, f"Expected 3 'United Kingdom', got {countries.count('United Kingdom')}"
    assert countries.count('France') == 2, f"Expected 2 'France', got {countries.count('France')}"
    
    # Check no old variants exist
    assert 'USA' not in countries, "'USA' should be standardized"
    assert 'US' not in countries, "'US' should be standardized"
    assert 'U.S.A.' not in countries, "'U.S.A.' should be standardized"
    assert 'canada' not in countries, "'canada' should be standardized"
    assert 'CAN' not in countries, "'CAN' should be standardized"
    assert 'UK' not in countries, "'UK' should be standardized"
    assert 'U.K.' not in countries, "'U.K.' should be standardized"
    assert 'FR' not in countries, "'FR' should be standardized"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
