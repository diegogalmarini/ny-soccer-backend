import sqlite3
import json

conn = sqlite3.connect('nycoedsoccer.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT name, text FROM league_websiteincludetext")
    rows = cursor.fetchall()
    print(json.dumps([{"name": r[0], "text": r[1]} for r in rows], indent=2))
except Exception as e:
    print(f"Error: {e}")

conn.close()
