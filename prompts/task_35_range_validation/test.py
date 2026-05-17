import pandas as pd
import os

def test():
    assert os.path.exists('validated.csv'), "Output file 'validated.csv' not found"
    
    df = pd.read_csv('validated.csv')
    
    assert len(df) == 6, f"Expected 6 rows, got {len(df)}"
    
    # Check age ranges
    assert df['age'].min() >= 0, f"Minimum age should be >= 0, got {df['age'].min()}"
    assert df['age'].max() <= 120, f"Maximum age should be <= 120, got {df['age'].max()}"
    
    # Check temperature ranges
    assert df['temperature'].min() >= 35.0, f"Minimum temperature should be >= 35.0, got {df['temperature'].min()}"
    assert df['temperature'].max() <= 42.0, f"Maximum temperature should be <= 42.0, got {df['temperature'].max()}"
    
    # Check specific invalid values are replaced
    bob_age = df[df['name'] == 'Bob']['age'].iloc[0]
    assert bob_age <= 120, f"Bob's age should be fixed, got {bob_age}"
    
    charlie_age = df[df['name'] == 'Charlie']['age'].iloc[0]
    assert charlie_age >= 0, f"Charlie's age should be fixed, got {charlie_age}"
    
    diana_temp = df[df['name'] == 'Diana']['temperature'].iloc[0]
    assert diana_temp <= 42.0, f"Diana's temperature should be fixed, got {diana_temp}"
    
    eve_temp = df[df['name'] == 'Eve']['temperature'].iloc[0]
    assert eve_temp >= 35.0, f"Eve's temperature should be fixed, got {eve_temp}"
    
    # Check valid values are unchanged
    alice = df[df['name'] == 'Alice'].iloc[0]
    assert alice['age'] == 25, "Alice's age should be unchanged"
    assert alice['temperature'] == 36.5, "Alice's temperature should be unchanged"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
