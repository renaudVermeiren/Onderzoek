import pandas as pd
import os

def test():
    assert os.path.exists('hourly_avg.csv'), "Output file 'hourly_avg.csv' not found"
    
    df = pd.read_csv('hourly_avg.csv')
    
    # Should have fewer rows than original (9 rows -> hourly groups)
    assert len(df) <= 3, f"Expected at most 3 hourly groups, got {len(df)}"
    
    # Check that value column exists and is numeric
    assert 'value' in df.columns, "Column 'value' should be present"
    assert df['value'].dtype in ['float64', 'float32', 'int64', 'int32'], f"Value should be numeric, got {df['value'].dtype}"
    
    # Check average is reasonable (around 11-13 range)
    avg_val = df['value'].mean()
    assert 10 <= avg_val <= 15, f"Average value should be between 10-15, got {avg_val}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
