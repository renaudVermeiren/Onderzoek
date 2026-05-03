import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('combined.csv'), "Output file 'combined.csv' not found"
    
    # Read output
    df = pd.read_csv('combined.csv')
    
    # Check columns
    expected_columns = ['id', 'date', 'revenue', 'expenses']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check all rows are present (3 per month * 3 months = 9)
    assert len(df) == 9, f"Expected 9 rows, got {len(df)}"
    
    # Check index is reset (0 to 8)
    assert list(df.index) == list(range(9)), f"Index should be 0-8, got {list(df.index)}"
    
    # Check all ids are present
    expected_ids = list(range(1, 10))
    actual_ids = sorted(df['id'].tolist())
    assert actual_ids == expected_ids, f"Expected ids {expected_ids}, got {actual_ids}"
    
    # Check specific values from different months
    jan_data = df[df['date'] == '2024-01-15']
    assert len(jan_data) == 1, "Should have 2024-01-15 data"
    assert jan_data['revenue'].iloc[0] == 1000, "Jan 15 revenue should be 1000"
    
    mar_data = df[df['date'] == '2024-03-25']
    assert len(mar_data) == 1, "Should have 2024-03-25 data"
    assert mar_data['revenue'].iloc[0] == 2800, "Mar 25 revenue should be 2800"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
