import pandas as pd
import os

def test():
    assert os.path.exists('cleaned.csv'), "Output file 'cleaned.csv' not found"
    
    df = pd.read_csv('cleaned.csv')
    
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    # Check no whitespace issues
    for col in df.columns:
        if df[col].dtype == 'object':
            for val in df[col]:
                str_val = str(val)
                assert str_val == str_val.strip(), f"Value '{str_val}' in column '{col}' has leading/trailing whitespace"
                assert '\t' not in str_val, f"Value '{str_val}' in column '{col}' contains tabs"
    
    # Check special chars removed from description
    for val in df['description']:
        assert '@' not in str(val), "Description should not contain @"
        assert '#' not in str(val), "Description should not contain #"
        assert '$' not in str(val), "Description should not contain $"
        assert '%' not in str(val), "Description should not contain %"
    
    # Check specific values
    desc_values = df['description'].tolist()
    assert 'Hello World' in desc_values, "'Hello World' should be present"
    assert 'Test data' in desc_values, "'Test data' should be present"
    assert 'Special chars' in desc_values, "'Special chars' should be present (without @#$%)"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
