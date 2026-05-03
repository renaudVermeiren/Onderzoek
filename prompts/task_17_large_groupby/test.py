import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('summary.csv'), "Output file 'summary.csv' not found"
    
    # Read output
    df = pd.read_csv('summary.csv')
    
    # Check columns
    expected_columns = ['category', 'total_sales']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check all 3 categories are present
    assert len(df) == 3, f"Expected 3 categories, got {len(df)}"
    
    # Check categories
    categories = df['category'].tolist()
    assert 'Electronics' in categories, "Electronics category should be in output"
    assert 'Clothing' in categories, "Clothing category should be in output"
    assert 'Food' in categories, "Food category should be in output"
    
    # Check totals (calculated from the data)
    # Electronics: 1500+2300+1800+2100+1650+2400 = 11750
    # Clothing: 800+1200+950+1100+880 = 4930
    # Food: 450+600+750+500 = 2300
    expected_totals = {
        'Electronics': 11750,
        'Clothing': 4930,
        'Food': 2300
    }
    
    for category, expected_total in expected_totals.items():
        actual_total = df[df['category'] == category]['total_sales'].iloc[0]
        assert actual_total == expected_total, \
            f"Expected total_sales for {category} to be {expected_total}, got {actual_total}"
    
    # Check sorting (descending by total_sales)
    totals = df['total_sales'].tolist()
    assert totals == sorted(totals, reverse=True), "Data should be sorted by total_sales descending"
    
    # Check Electronics is first (highest total)
    assert df.iloc[0]['category'] == 'Electronics', "Electronics should be first (highest sales)"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
