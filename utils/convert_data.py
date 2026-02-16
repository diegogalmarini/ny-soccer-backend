
import re

def convert_data(input_file, output_file):
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f_in:
        # Read line by line to handle large files better
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                if line.startswith('INSERT INTO'):
                    # 1. Convert backticks to quotes or remove
                    line = line.replace('`', '"')
                    
                    # 2. Escape strings: \' -> '' (Postgres specific)
                    # Be careful not to replace \\'
                    # Simple replace might be risky but good enough for standard dumps
                    line = line.replace("\\'", "''")
                    
                    # 3. Handle binary/hex data? (MySQL uses 0x..., Postgres requires decode or bytea)
                    # If dump uses X'...' or 0x..., we need conversion for bytea columns.
                    # Assuming mostly text for now.
                    
                    # 4. Handle invalid dates '0000-00-00 00:00:00' -> NULL or specific date
                    line = line.replace("'0000-00-00 00:00:00'", "NULL")
                    line = line.replace("'0000-00-00'", "NULL")
                    
                    f_out.write(line)

    print(f"Data extraction complete. Saved to {output_file}")

if __name__ == '__main__':
    convert_data('database_full_2026.sql', 'data_pg_converted.sql')
