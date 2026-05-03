import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check row count (3 rows expected)
    assert len(df) == 3, f"Expected 3 rows, got {len(df)}"
    
    # Check no nulls in user_id column
    null_user_ids = df['user_id'].isnull().sum()
    assert null_user_ids == 0, f"There are {null_user_ids} null values in user_id"
    
    # Check no nulls in timestamp column
    null_timestamps = df['timestamp'].isnull().sum()
    assert null_timestamps == 0, f"There are {null_timestamps} null values in timestamp"
    
    # Check specific user_ids present (1, 3, 5)
    expected_users = {1, 3, 5}
    actual_users = set(df['user_id'].values)
    assert actual_users == expected_users, f"Expected users {expected_users}, got {actual_users}"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
