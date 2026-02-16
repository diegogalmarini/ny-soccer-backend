import sqlite3
import json

conn = sqlite3.connect('nycoedsoccer.db')
cursor = conn.cursor()

data = {}

try:
    cursor.execute("SELECT name, text FROM league_websiteincludetext")
    rows = cursor.fetchall()
    data['website_include_text'] = [{"name": r[0], "text": r[1]} for r in rows]
    
    cursor.execute("SELECT url, title, content FROM django_flatpage")
    data['flatpages'] = [{"url": r[0], "title": r[1], "content": r[2]} for r in cursor.fetchall()]

    with open('content_audit.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Audit data written to content_audit.json")
except Exception as e:
    print(f"Error: {e}")

conn.close()
