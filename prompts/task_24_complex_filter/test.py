import pandas as pd
import os

def test():
    assert os.path.exists('filtered_complex.csv'), "Output file 'filtered_complex.csv' not found"
    
    df = pd.read_csv('filtered_complex.csv')
    
    assert len(df) == 4, f"Expected 4 rows, got {len(df)}"
    
    names = df['name'].tolist()
    assert 'John Smith' in names, "John Smith should be in output (IT, 35)"
    assert 'Mike Brown' in names, "Mike Brown should be in output (IT, 42)"
    assert 'Chris Wilson' in names, "Chris Wilson should be in output (IT, 45)"
    assert 'David Martinez' in names, "David Martinez should be in output (Sales, 5100, 7y)"
    
    assert 'Sarah Johnson' not in names, "Sarah Johnson should NOT be in output (Marketing, not IT, salary <=5000)"
    assert 'Emily Davis' not in names, "Emily Davis should NOT be in output (Sales, salary <=5000)"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
