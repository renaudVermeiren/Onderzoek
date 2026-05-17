import pandas as pd
import os
import numpy as np

def test():
    assert os.path.exists('converted.csv'), "Output file 'converted.csv' not found"
    
    df = pd.read_csv('converted.csv')
    
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    # Check price is float
    assert df['price'].dtype in ['float64', 'float32'], f"Price should be float, got {df['price'].dtype}"
    
    # Check quantity is int
    assert df['quantity'].dtype in ['int64', 'int32', 'int16', 'int8'], f"Quantity should be int, got {df['quantity'].dtype}"
    
    # Check specific values
    assert abs(df.loc[0, 'price'] - 1299.99) < 0.01, "First price should be 1299.99"
    assert df.loc[1, 'quantity'] == 10, "Second quantity should be 10"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
