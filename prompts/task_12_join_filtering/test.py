import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check columns
    expected_columns = ['user_id', 'name', 'order_count']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check only users with >1 order are present
    assert len(df) == 2, f"Expected 2 users (>1 order), got {len(df)}"
    
    # Check Charlie is NOT in output
    assert 'Charlie' not in df['name'].values, "Charlie should not be in output (only 1 order)"
    
    # Check order counts
    expected_counts = {'Alice': 3, 'Bob': 2}
    for name, expected_count in expected_counts.items():
        actual_count = df[df['name'] == name]['order_count'].iloc[0]
        assert actual_count == expected_count, f"Expected order_count for {name} to be {expected_count}, got {actual_count}"
    
    # Check sorting (descending by order_count)
    counts = df['order_count'].tolist()
    assert counts == sorted(counts, reverse=True), "Data should be sorted by order_count descending"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
