import pandas as pd
import os

def test():
    assert os.path.exists('valid_orders.csv'), "Output file 'valid_orders.csv' not found"
    assert os.path.exists('invalid_orders.csv'), "Output file 'invalid_orders.csv' not found"
    
    valid = pd.read_csv('valid_orders.csv')
    invalid = pd.read_csv('invalid_orders.csv')
    
    assert len(valid) == 4, f"Expected 4 valid orders, got {len(valid)}"
    assert len(invalid) == 2, f"Expected 2 invalid orders, got {len(invalid)}"
    
    # Check valid orders
    valid_ids = valid['id'].tolist()
    assert 1 in valid_ids, "Order 1 should be valid"
    assert 5 in valid_ids, "Order 5 should be valid"
    assert 6 in valid_ids, "Order 6 should be valid"
    
    # Check invalid orders
    invalid_ids = invalid['id'].tolist()
    assert 2 in invalid_ids, "Order 2 (invalid email) should be invalid"
    assert 3 in invalid_ids, "Order 3 (negative amount) should be invalid"
    
    # Check validation_error column
    assert 'validation_error' in invalid.columns, "invalid_orders should have 'validation_error' column"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
