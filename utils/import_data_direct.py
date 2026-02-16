import os
import re
import sys
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# This script parses a MySQL dump and pushes data via direct PostgreSQL connection
# It handles MySQL-specific syntax and converts types (e.g. TinyInt(1) -> Boolean)

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

SQL_FILE = r"r:\Trabajos\NY Soccer\NY_Soccer_2026\database_full_2026.sql"

# Tables that need boolean conversion
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
    tables = {}
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
            if in_parens or in_quote:
                current_val += char
        i += 1
        
    return rows

def clean_val(val, col_name, table_name):
    if val is None: return None
    if isinstance(val, str):
        val = val.strip()
        if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
            val = val[1:-1]
        val = val.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n").replace("\\r", "\r")
            
    if table_name in BOOLEAN_COLS and col_name in BOOLEAN_COLS[table_name]:
        if val in ('1', 1, True, 'True', 't'): return True
        if val in ('0', 0, False, 'False', 'f'): return False
        
    return val

def process_migration():
    print(f"📂 Reading {SQL_FILE}...")
    if not os.path.exists(SQL_FILE):
        print(f"❌ SQL File not found at {SQL_FILE}")
        return
        
    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    table_schemas = parse_create_tables(content)
    insert_pattern = re.compile(r'INSERT INTO [`"]?([\w_]+)[`"]? VALUES (.*?);', re.DOTALL | re.IGNORECASE)
    matches = insert_pattern.findall(content)
    
    db_pass = os.environ.get("DB_PASSWORD")
    db_user = "postgres.gbulbdoewytbvxxmwsur" # Using pooling format user@projectref for pooler if needed, let me try direct postgres first
    db_host = "aws-0-us-west-2.pooler.supabase.com"
    db_port = 6543
    db_name = "postgres"
    
    print(f"🚀 Found {len(matches)} data blocks. Connecting to DB {db_host}:{db_port}...")
    
    conn = None
    cur = None
    try:
        # Note: When using pooler, user must be "postgres.project_ref" for some modes
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            sslmode='require'
        )
        conn.autocommit = False
        cur = conn.cursor()
        
        # Disable constraints temporarily to allow any order
        print("🛠️  Disabling constraints for import session...")
        cur.execute("SET session_replication_role = 'replica';")
        
        for table, values_str in matches:
            clean_table = table.strip('`"')
            if clean_table not in table_schemas:
                # print(f"⚠️  Skipping {table} (Schema not found)")
                continue
            
            cols = table_schemas[clean_table]
            print(f"⚡ Processing {clean_table}...")
            
            raw_rows = get_rows_from_insert(values_str)
            data_to_insert = []
            for row in raw_rows:
                if len(row) != len(cols): continue
                cleaned_row = tuple(clean_val(row[i], cols[i], clean_table) for i in range(len(cols)))
                data_to_insert.append(cleaned_row)
            
            if data_to_insert:
                col_names = ",".join([f'"{c}"' for c in cols])
                query = f'INSERT INTO "{clean_table}" ({col_names}) VALUES %s ON CONFLICT DO NOTHING'
                execute_values(cur, query, data_to_insert)
                print(f"   ✅ Inserted {len(data_to_insert)} rows.")
        
        print("🛠️  Re-enabling constraints...")
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"🔥 Critical Migration Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    process_migration()
