import os
import re
import sys
import ast
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# This script parses a MySQL dump and pushes data via Supabase API (Postgrest)
# It handles MySQL-specific syntax and converts types (e.g. TinyInt(1) -> Boolean)

# Increase field size limit for large inserts
import csv
csv.field_size_limit(sys.maxsize)

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

# Supabase config
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(url, key)

# Path to the MySQL dump
SQL_FILE = r"r:\Trabajos\NY Soccer\NY_Soccer_2026\database_full_2026.sql"

# Tables that need boolean conversion (TinyInt(1) in MySQL -> Boolean in PG)
BOOLEAN_COLS = {
    'auth_user': ['is_superuser', 'is_staff', 'is_active'],
    'league_externalleague': ['active'],
    'league_legacyleague': ['active'],
    'league_match': ['rescheduled'],
    'league_team': ['override_payment'],
    'league_teamplayer': ['is_captain', 'override_payment'],
    'league_player': ['interested_in_brooklyn_leagues', 'interested_in_manhattan_leagues', 'interested_in_soccer_school'],
    'django_celery_beat_periodictask': ['enabled'],
    'django_celery_results_taskresult': ['hidden'],
    'django_flatpage': ['enable_comments', 'registration_required'],
    'paypal_ipn': ['test_ipn', 'flag'],
}

def parse_create_tables(content):
    """
    Extract column names from CREATE TABLE statements.
    """
    tables = {}
    # Find all CREATE TABLE blocks
    matches = re.finditer(r'CREATE TABLE [`"]?(\w+)[`"]?\s*\((.*?)\)\s*(?:ENGINE|;)', content, re.DOTALL | re.IGNORECASE)
    for m in matches:
        table_name = m.group(1)
        body = m.group(2)
        cols = []
        for line in body.split('\n'):
            line = line.strip()
            if not line or line.startswith(('KEY', 'PRIMARY KEY', 'UNIQUE KEY', 'CONSTRAINT')):
                continue
            m_col = re.search(r'^[`"]?(\w+)[`"]?', line)
            if m_col:
                cols.append(m_col.group(1))
        tables[table_name] = cols
    return tables

def get_rows_from_insert(values_str):
    """
    Robustly parses the VALUES (...) string.
    Handles nested commas in strings and escaped quotes.
    """
    # This regex finds balanced parentheses content: (val1, val2, ...), (val1, ...)
    # Simplified approach: Use a generator to yield characters and keep track of quotes
    rows = []
    current_row = []
    current_val = ""
    in_quote = False
    quote_char = None
    escape = False
    in_parens = False
    
    i = 0
    while i < len(values_str):
        char = values_str[i]
        
        if escape:
            current_val += char
            escape = False
        elif char == '\\':
            escape = True
        elif char in ("'", '"'):
            if not in_quote:
                in_quote = True
                quote_char = char
            elif char == quote_char:
                # Check for doubled quote (MySQL style escape)
                if i + 1 < len(values_str) and values_str[i+1] == char:
                    current_val += char
                    i += 1
                else:
                    in_quote = False
                    quote_char = None
            else:
                current_val += char
        elif char == '(' and not in_quote:
            in_parens = True
            current_row = []
        elif char == ')' and not in_quote:
            in_parens = False
            # Finish last value
            val = current_val.strip()
            if val.upper() == 'NULL': rows.append(current_row + [None])
            else: rows.append(current_row + [val])
            current_val = ""
        elif char == ',' and not in_quote:
            if in_parens:
                val = current_val.strip()
                if val.upper() == 'NULL': current_row.append(None)
                else: current_row.append(val)
                current_val = ""
            else:
                # Between rows
                pass
        else:
            if in_parens or in_quote:
                current_val += char
        i += 1
        
    return rows

def clean_val(val, col_name, table_name):
    if val is None: return None
    # Remove quotes from string values if they were captured
    if isinstance(val, str):
        val = val.strip()
        if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
            val = val[1:-1]
            # Unescape
            val = val.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n").replace("\\r", "\r")
            
    # Boolean conversion
    if table_name in BOOLEAN_COLS and col_name in BOOLEAN_COLS[table_name]:
        if val in ('1', 1, True, 'True', 't'): return True
        if val in ('0', 0, False, 'False', 'f'): return False
        
    return val

def process_file():
    print(f"📂 Reading {SQL_FILE}...")
    if not os.path.exists(SQL_FILE):
        print("❌ File not found."); return

    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    print("🔎 Parsing Schema...")
    table_schemas = parse_create_tables(content)
    
    # Order of insertion to respect foreign keys (simplified)
    # We should look for INSERTs in the file.
    insert_pattern = re.compile(r'INSERT INTO [`"]?([\w_]+)[`"]? VALUES (.*?);', re.DOTALL | re.IGNORECASE)
    matches = insert_pattern.findall(content)
    
    print(f"🚀 Starting Migration of {len(matches)} table data blocks...")
    
    for table, values_str in matches:
        if table not in table_schemas:
            # Maybe it's quoted differently
            clean_table = table.strip('`"')
            if clean_table in table_schemas: table = clean_table
            else:
                print(f"⚠️  Skipping {table} (Schema not found)")
                continue
                
        cols = table_schemas[table]
        print(f"⚡ Processing {table}...")
        
        # Robust parsing
        raw_rows = get_rows_from_insert(values_str)
        # Actually a list of lists of values
        
        data_payload = []
        for r_idx, row in enumerate(raw_rows):
            if len(row) != len(cols):
                print(f"   ❌ Column mismatch in {table} row {r_idx}: expected {len(cols)}, got {len(row)}")
                continue
            
            item = {}
            for c_idx, col in enumerate(cols):
                item[col] = clean_val(row[c_idx], col, table)
            data_payload.append(item)
            
        if not data_payload:
            continue
            
        # Batch insert
        batch_size = 500
        for i in range(0, len(data_payload), batch_size):
            batch = data_payload[i:i+batch_size]
            try:
                # Use upsert to be idempotent
                supabase.table(table).upsert(batch).execute()
                print(f"   ✅ {table}: rows {i} to {min(i+batch_size, len(data_payload))}")
            except Exception as e:
                print(f"   🔥 Error in {table}: {e}")
                # Log detailed error if needed
                # print(f"   Sample data: {batch[0]}")

if __name__ == "__main__":
    process_file()
