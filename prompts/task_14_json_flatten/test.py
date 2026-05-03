import pandas as pd
import os

def test():
    # Check if output file exists
    assert os.path.exists('flat_data.csv'), "Output file 'flat_data.csv' not found"
    
    # Read output
    df = pd.read_csv('flat_data.csv')
    
    # Check columns (allow different naming conventions)
    expected_columns = {'id', 'name', 'email', 'address_street', 'address_city', 'address_country'}
    actual_columns = set(df.columns)
    
    # Check if all expected columns are present (may have prefixes like 'address.')
    has_street = 'address_street' in actual_columns or 'address.street' in actual_columns
    has_city = 'address_city' in actual_columns or 'address.city' in actual_columns
    has_country = 'address_country' in actual_columns or 'address.country' in actual_columns
    
    assert 'id' in actual_columns, "Column 'id' not found"
    assert 'name' in actual_columns, "Column 'name' not found"
    assert 'email' in actual_columns, "Column 'email' not found"
    assert has_street, "Address street column not found"
    assert has_city, "Address city column not found"
    assert has_country, "Address country column not found"
    
    # Check all users are present
    assert len(df) == 3, f"Expected 3 users, got {len(df)}"
    
    # Check specific data
    alice = df[df['name'] == 'Alice Johnson']
    assert len(alice) == 1, "Alice should be in output"
    
    # Get street column name (may vary)
    street_col = 'address_street' if 'address_street' in df.columns else 'address.street'
    city_col = 'address_city' if 'address_city' in df.columns else 'address.city'
    country_col = 'address_country' if 'address_country' in df.columns else 'address.country'
    
    assert alice[street_col].iloc[0] == '123 Main St', f"Alice street should be '123 Main St'"
    assert alice[city_col].iloc[0] == 'New York', f"Alice city should be 'New York'"
    assert alice[country_col].iloc[0] == 'USA', f"Alice country should be 'USA'"
    
    print("All tests passed!")

if __name__ == "__main__":
    test()
