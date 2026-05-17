import pandas as pd
import os
import numpy as np

def test():
    assert os.path.exists('cleaned.csv'), "Output file 'cleaned.csv' not found"
    
    df = pd.read_csv('cleaned.csv')
    
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    # Check types are numeric
    assert df['price'].dtype in ['float64', 'float32', 'int64', 'int32'], f"Price should be numeric, got {df['price'].dtype}"
    assert df['percentage'].dtype in ['float64', 'float32', 'int64', 'int32'], f"Percentage should be numeric, got {df['percentage'].dtype}"
    assert df['temperature'].dtype in ['float64', 'float32', 'int64', 'int32'], f"Temperature should be numeric, got {df['temperature'].dtype}"
    
    # Check specific values
    assert abs(df.loc[0, 'price'] - 1250.0) < 0.01, f"Row 1 price should be 1250.0, got {df.loc[0, 'price']}"
    assert abs(df.loc[1, 'price'] - 2500.0) < 0.01, f"Row 2 price should be 2500.0, got {df.loc[1, 'price']}"
    assert df.loc[0, 'percentage'] == 50.0, f"Row 1 percentage should be 50.0, got {df.loc[0, 'percentage']}"
    assert df.loc[2, 'percentage'] == 100.0, f"Row 3 percentage should be 100.0, got {df.loc[2, 'percentage']}"
    assert df.loc[0, 'temperature'] == 25.0, f"Row 1 temperature should be 25.0, got {df.loc[0, 'temperature']}"
    assert df.loc[2, 'temperature'] == -5.0, f"Row 3 temperature should be -5.0, got {df.loc[2, 'temperature']}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
