import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check no nulls remain
    assert not df.isnull().any().any(), "There are still null values in the output"
    
    # Check age column filled with mean (27.5)
    expected_mean = 27.5
    actual_filled_age = df.loc[df['user_id'] == 2, 'age'].iloc[0]
    assert round(actual_filled_age, 1) == expected_mean, f"Age should be filled with mean {expected_mean}, got {actual_filled_age}"
    
    # Check city column filled with mode (Brussels)
    expected_mode = 'Brussels'
    actual_filled_city = df.loc[df['user_id'] == 3, 'city'].iloc[0]
    assert actual_filled_city == expected_mode, f"City should be filled with mode '{expected_mode}', got '{actual_filled_city}'"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
