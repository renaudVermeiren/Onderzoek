import pandas as pd
import os

def test():
    assert os.path.exists('output.csv'), "Output file not found"
    
    df = pd.read_csv('output.csv')
    
    # Should have 3 rows
    assert len(df) == 3, f"Expected 3 rows, got {len(df)}"
    
    # Check required columns
    required_cols = ['user_name', 'product_name', 'quantity', 'total_price']
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check Alice has 2 products
    alice_rows = df[df['user_name'] == 'Alice']
    assert len(alice_rows) == 2, f"Alice should have 2 products, got {len(alice_rows)}"
    
    # Check Bob has 1 product
    bob_rows = df[df['user_name'] == 'Bob']
    assert len(bob_rows) == 1, f"Bob should have 1 product, got {len(bob_rows)}"
    
    # Check total_price calculation
    alice_laptop = df[(df['user_name'] == 'Alice') & (df['product_name'] == 'Laptop')]
    if len(alice_laptop) > 0:
        expected_price = 2 * 1000  # quantity 2 * price 1000
        actual_price = alice_laptop['total_price'].iloc[0]
        assert actual_price == expected_price, f"Alice Laptop total_price should be {expected_price}, got {actual_price}"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
