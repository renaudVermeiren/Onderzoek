import pandas as pd
import os

def test():
    assert os.path.exists('clean_data.csv'), "Output file 'clean_data.csv' not found"
    
    df = pd.read_csv('clean_data.csv')
    
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    expected_columns = ['name', 'age', 'department', 'salary']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    assert 'John Doe' in df['name'].values, "John Doe should be in data"
    assert df.loc[df['name'] == 'Jane Smith', 'age'].iloc[0] == 30, "Jane Smith age should be 30"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
