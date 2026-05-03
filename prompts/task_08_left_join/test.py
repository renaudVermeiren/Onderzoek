import pandas as pd
import os

def test():
    assert os.path.exists('output.csv'), "Output file not found"
    
    df = pd.read_csv('output.csv')
    
    # Should have 3 rows (all users)
    assert len(df) == 3, f"Expected 3 rows (all users), got {len(df)}"
    
    # Check all users present
    assert set(df['user_id'].values) == {1, 2, 3}, "All 3 users should be present"
    
    # Check total_spend values
    alice_spend = df[df['name'] == 'Alice']['total_spend'].iloc[0]
    bob_spend = df[df['name'] == 'Bob']['total_spend'].iloc[0]
    charlie_spend = df[df['name'] == 'Charlie']['total_spend'].iloc[0]
    
    assert alice_spend == 300, f"Alice should have total_spend 300, got {alice_spend}"
    assert bob_spend == 150, f"Bob should have total_spend 150, got {bob_spend}"
    assert charlie_spend == 0, f"Charlie should have total_spend 0, got {charlie_spend}"
    
    # Check no nulls in total_spend
    assert df['total_spend'].notna().all(), "No nulls allowed in total_spend"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
