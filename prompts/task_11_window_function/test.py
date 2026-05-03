import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check columns
    expected_columns = ['order_id', 'user_id', 'order_date', 'amount', 'rank']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check all orders are present
    assert len(df) == 6, f"Expected 6 orders, got {len(df)}"
    
    # Check rank values for user 1 (dates: 2024-05-10, 2024-03-15, 2024-01-20)
    user1_orders = df[df['user_id'] == 1].sort_values('rank')
    assert list(user1_orders['rank']) == [1, 2, 3], "User 1 ranks should be 1, 2, 3"
    assert user1_orders[user1_orders['rank'] == 1]['order_date'].iloc[0] == '2024-05-10', "User 1 rank 1 should be 2024-05-10"
    
    # Check rank values for user 2 (dates: 2024-04-05, 2024-02-28)
    user2_orders = df[df['user_id'] == 2].sort_values('rank')
    assert list(user2_orders['rank']) == [1, 2], "User 2 ranks should be 1, 2"
    assert user2_orders[user2_orders['rank'] == 1]['order_date'].iloc[0] == '2024-04-05', "User 2 rank 1 should be 2024-04-05"
    
    # Check sorting (user_id, then rank)
    expected_order = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 1)]
    actual_order = list(zip(df['user_id'].tolist(), df['rank'].tolist()))
    assert actual_order == expected_order, f"Expected order {expected_order}, got {actual_order}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
