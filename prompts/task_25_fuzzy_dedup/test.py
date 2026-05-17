import pandas as pd
import os

def test():
    assert os.path.exists('deduplicated.csv'), "Output file 'deduplicated.csv' not found"
    
    df = pd.read_csv('deduplicated.csv')
    
    assert len(df) == 4, f"Expected 4 rows (4 unique customers), got {len(df)}"
    
    names = df['name'].tolist()
    assert 'John Smith' in names, "John Smith should be kept (first occurrence)"
    assert 'Jane Doe' in names, "Jane Doe should be kept (first occurrence)"
    assert 'Bob Wilson' in names, "Bob Wilson should be kept (first occurrence)"
    assert 'Alice Brown' in names, "Alice Brown should be kept"
    
    assert 'Jon Smith' not in names, "Jon Smith should be removed (duplicate)"
    assert 'Jan Doe' not in names, "Jan Doe should be removed (duplicate)"
    assert 'Robert Wilson' not in names, "Robert Wilson should be removed (duplicate)"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
