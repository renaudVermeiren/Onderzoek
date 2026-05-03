import pandas as pd
import os
import re

def test():
    # Check if output file exists
    assert os.path.exists('output.csv'), "Output file 'output.csv' not found"
    
    # Read output
    df = pd.read_csv('output.csv')
    
    # Check 3 rows in output (2 valid rows + header)
    assert len(df) == 2, f"Expected 2 rows (invalid email removed), got {len(df)}"
    
    # Check all emails are lowercase
    for email in df['email']:
        assert email == email.lower(), f"Email '{email}' is not lowercase"
    
    # Check no leading/trailing whitespace in text columns
    for col in ['name', 'email', 'city']:
        for val in df[col]:
            str_val = str(val)
            assert str_val == str_val.strip(), f"Value '{str_val}' in column '{col}' has whitespace"
    
    # Check specific transformations
    alice_row = df[df['id'] == 1]
    assert len(alice_row) == 1, "Alice row should exist"
    assert alice_row['email'].iloc[0] == 'alice@example.com', "Email should be lowercase"
    assert alice_row['name'].iloc[0] == 'Alice', "Name should be 'Alice' without whitespace"
    assert alice_row['city'].iloc[0] == 'Brussels', "City should be 'Brussels' without whitespace"
    
    # Check invalid email row is removed
    assert 2 not in df['id'].values, "Row with invalid email (id=2) should be removed"
    
    # Check Charlie row exists and is correct
    charlie_row = df[df['id'] == 3]
    assert len(charlie_row) == 1, "Charlie row should exist"
    assert charlie_row['email'].iloc[0] == 'charlie@test.org', "Charlie email incorrect"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test()
