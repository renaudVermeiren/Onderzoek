import pandas as pd
import os

def test():
    assert os.path.exists('output.csv'), "Output file not found"
    
    df = pd.read_csv('output.csv')
    
    # Should have 3 rows (2 orders for Alice, 1 for Bob)
    assert len(df) == 3, f"Expected 3 rows, got {len(df)}"
    
    # Should have users 1 and 2, not 3
    user_ids = set(df['user_id'].values)
    assert user_ids == {1, 2}, f"Expected users 1 and 2, got {user_ids}"
    
    # Charlie should not be in output
    assert 'Charlie' not in df['name'].values, "Charlie should not appear in inner join result"
    
    # Check columns from both tables exist
    assert 'name' in df.columns, "Name column from users should exist"
    assert 'amount' in df.columns, "Amount column from orders should exist"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
