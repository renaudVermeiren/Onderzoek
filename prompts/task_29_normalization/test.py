import pandas as pd
import os

def test():
    assert os.path.exists('normalized.csv'), "Output file 'normalized.csv' not found"
    
    df = pd.read_csv('normalized.csv')
    
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    # Check score columns are between 0 and 1
    for col in ['math_score', 'science_score', 'english_score']:
        assert col in df.columns, f"Column '{col}' should be present"
        assert df[col].min() >= 0, f"{col} minimum should be >= 0"
        assert df[col].max() <= 1, f"{col} maximum should be <= 1"
    
    # Check Alice's math is highest (85/90 = ~0.94) - wait, no, 90 is max
    # Alice: 85, Charlie: 90, so Alice should be ~0.833, Charlie = 1.0
    charlie_math = df[df['student'] == 'Charlie']['math_score'].iloc[0]
    assert abs(charlie_math - 1.0) < 0.01, "Charlie's math should be normalized to 1.0 (max score)"
    
    # Check Diana's math is lowest (65)
    diana_math = df[df['student'] == 'Diana']['math_score'].iloc[0]
    assert abs(diana_math - 0.0) < 0.01, "Diana's math should be normalized to 0.0 (min score)"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
