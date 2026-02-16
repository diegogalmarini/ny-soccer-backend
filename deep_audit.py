import sqlite3
import json

conn = sqlite3.connect('nycoedsoccer.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            col_name = col[1]
            if 'text' in col[2].lower() or 'char' in col[2].lower() or 'blob' in col[2].lower():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} LIKE '%\\r%' OR {col_name} LIKE '%\\n%'")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"Table: {table_name}, Column: {col_name} has {count} rows with potential literal backslashes")
except Exception as e:
    print(f"Error: {e}")

conn.close()
