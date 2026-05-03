import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check row count (3 rows expected)
    assert len(df) == 3, f"Expected 3 rows, got {len(df)}"
    
    # Check that for user 1, order 101, the latest timestamp is kept
    user1_order101 = df[(df['user_id'] == 1) & (df['order_id'] == 101)]
    assert len(user1_order101) == 1, "Should have exactly 1 row for user 1, order 101"
    assert user1_order101['timestamp'].iloc[0] == '2024-02-01', "Should keep the latest timestamp (2024-02-01)"
    assert user1_order101['amount'].iloc[0] == 150.0, "Amount should be 150.0 for the latest entry"
    
    # Check both user 2 orders are kept
    user2_rows = df[df['user_id'] == 2]
    assert len(user2_rows) == 2, "Should have 2 rows for user 2 (different orders)"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
