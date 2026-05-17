import pandas as pd
import os

def test():
    assert os.path.exists('pivot_output.csv'), "Output file 'pivot_output.csv' not found"
    
    df = pd.read_csv('pivot_output.csv')
    
    # Should have product column + region columns
    assert 'product' in df.columns, "Column 'product' should be the index/row"
    
    # Check regions are columns
    regions = ['North', 'South', 'East', 'West']
    for region in regions:
        assert region in df.columns, f"Region '{region}' should be a column"
    
    # Check specific values
    laptop_row = df[df['product'] == 'Laptop']
    assert len(laptop_row) == 1, "Laptop should have one row"
    assert laptop_row['North'].iloc[0] == 1200, "Laptop North should be 1200"
    assert laptop_row['South'].iloc[0] == 1200, "Laptop South should be 1200"
    assert laptop_row['East'].iloc[0] == 1200, "Laptop East should be 1200"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
