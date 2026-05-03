import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check columns
    expected_columns = ['user_id', 'name', 'total_spend']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check all users are present
    assert len(df) == 3, f"Expected 3 users, got {len(df)}"
    
    # Check total_spend values
    expected_totals = {'Alice': 350, 'Bob': 250, 'Charlie': 400}
    for name, expected_total in expected_totals.items():
        actual_total = df[df['name'] == name]['total_spend'].iloc[0]
        assert actual_total == expected_total, f"Expected total_spend for {name} to be {expected_total}, got {actual_total}"
    
    # Check sorting (descending by total_spend)
    totals = df['total_spend'].tolist()
    assert totals == sorted(totals, reverse=True), "Data should be sorted by total_spend descending"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
