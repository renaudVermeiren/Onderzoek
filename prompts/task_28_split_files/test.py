import pandas as pd
import os

def test():
    assert os.path.exists('category_A.csv'), "Output file 'category_A.csv' not found"
    assert os.path.exists('category_B.csv'), "Output file 'category_B.csv' not found"
    assert os.path.exists('category_C.csv'), "Output file 'category_C.csv' not found"
    
    df_a = pd.read_csv('category_A.csv')
    df_b = pd.read_csv('category_B.csv')
    df_c = pd.read_csv('category_C.csv')
    
    assert len(df_a) == 2, f"Expected 2 rows in category A, got {len(df_a)}"
    assert len(df_b) == 2, f"Expected 2 rows in category B, got {len(df_b)}"
    assert len(df_c) == 2, f"Expected 2 rows in category C, got {len(df_c)}"
    
    assert 'Alice' in df_a['name'].values, "Alice should be in category A"
    assert 'Charlie' in df_a['name'].values, "Charlie should be in category A"
    
    assert 'Bob' in df_b['name'].values, "Bob should be in category B"
    assert 'Eve' in df_b['name'].values, "Eve should be in category B"
    
    assert 'David' in df_c['name'].values, "David should be in category C"
    assert 'Frank' in df_c['name'].values, "Frank should be in category C"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
