import sqlite3
import json

conn = sqlite3.connect('nycoedsoccer.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT id, name, league_description FROM league_league")
    leagues = cursor.fetchall()
    for l_id, name, desc in leagues:
        if desc and ('\\r' in desc or '\\n' in desc):
            print(f"League ID: {l_id}, Name: {name} contains literal backslashes in description")
            print(f"Description sample: {desc[:100]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
