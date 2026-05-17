import pandas as pd
import os

def test():
    assert os.path.exists('ranked.csv'), "Output file 'ranked.csv' not found"
    
    df = pd.read_csv('ranked.csv')
    
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    # Check rank column exists
    assert 'rank' in df.columns, "Column 'rank' should be present"
    
    # Check sorting order
    assert df['rank'].iloc[0] == 1, "First row should have rank 1"
    
    # Alice should be first (grade 92, age 20)
    first_student = df.iloc[0]
    assert first_student['name'] == 'Alice', f"First student should be Alice, got {first_student['name']}"
    assert first_student['grade'] == 92, "Alice should have grade 92"
    
    # Charlie should be second (grade 92, age 21 - older than Alice)
    second_student = df.iloc[1]
    assert second_student['name'] == 'Charlie', f"Second student should be Charlie, got {second_student['name']}"
    
    # Diana should be third (grade 88)
    third_student = df.iloc[2]
    assert third_student['name'] == 'Diana', f"Third student should be Diana, got {third_student['name']}"
    
    # Check ranks are sequential
    ranks = df['rank'].tolist()
    assert ranks == [1, 2, 3, 4, 5], f"Ranks should be 1-5, got {ranks}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
