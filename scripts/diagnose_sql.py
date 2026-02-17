import os
import sys
import psycopg2
from urllib.parse import urlparse

# Simple script to check League 421 data without Django overhead
# Usage: python scripts/diagnose_sql.py <DATABASE_URL>

def diagnose(db_url):
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("Connected to database.")
        
        # Check League 421
        print("\nChecking League 421...")
        cur.execute("SELECT id, name, status FROM league_league WHERE id = 421;")
        league = cur.fetchone()
        if league:
            print(f"League Found: ID={league[0]}, Name='{league[1]}', Status={league[2]}")
        else:
            print("League 421 NOT FOUND.")
            return

        # Check Divisions
        print("\nChecking Divisions for League 421...")
        cur.execute("SELECT id, name FROM league_division WHERE league_id = 421;")
        divisions = cur.fetchall()
        print(f"Divisions details ({len(divisions)}):")
        for div in divisions:
            print(f"  - ID={div[0]}, Name='{div[1]}'")
            
            # Check Teams in Division
            cur.execute(f"SELECT id, name FROM league_team WHERE league_id = 421 AND division_id = {div[0]};")
            div_teams = cur.fetchall()
            print(f"    Teams in Division {div[1]} ({len(div_teams)}):")
            for t in div_teams:
                print(f"      - ID={t[0]}, Name='{t[1]}'")

        # Check Teams without Division (or all teams for league)
        print("\nChecking All Teams for League 421...")
        cur.execute("SELECT id, name, division_id FROM league_team WHERE league_id = 421;")
        all_teams = cur.fetchall()
        print(f"Total Teams: {len(all_teams)}")
        
        # Check Matches
        print("\nChecking Matches for League 421...")
        # Matches are linked via Round
        cur.execute("""
            SELECT m.id, m.status, r.name 
            FROM league_match m 
            JOIN league_round r ON m.round_id = r.id 
            WHERE r.league_id = 421;
        """)
        matches = cur.fetchall()
        print(f"Total Matches: {len(matches)}")
        completed = [m for m in matches if m[1] == 'Completed'] 
        print(f"Completed Matches: {len(completed)}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    else:
        # Default or read from env if not passed
        # But for safety, I'll pass it from command line argument when running
        print("Please provide DATABASE_URL")
        sys.exit(1)
        
    diagnose(db_url)
