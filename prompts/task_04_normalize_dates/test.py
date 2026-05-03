import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check all 5 rows present
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    # Check all dates are in YYYY-MM-DD format
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    for idx, row in df.iterrows():
        date_val = str(row['date'])
        assert re.match(date_pattern, date_val), f"Date '{date_val}' is not in YYYY-MM-DD format"
    
    # Check specific conversions
    assert df.loc[df['id'] == 1, 'date'].iloc[0] == '2024-01-01', "Row 1 date incorrect"
    assert df.loc[df['id'] == 2, 'date'].iloc[0] == '2024-02-15', "Row 2 should be converted from 15/02/2024 to 2024-02-15"
    assert df.loc[df['id'] == 3, 'date'].iloc[0] == '2024-03-25', "Row 3 should be converted from 03-25-2024 to 2024-03-25"
    assert df.loc[df['id'] == 4, 'date'].iloc[0] == '2024-04-10', "Row 4 date incorrect"
    assert df.loc[df['id'] == 5, 'date'].iloc[0] == '2024-05-30', "Row 5 should be converted from 30/05/2024 to 2024-05-30"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
