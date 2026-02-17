# Django setup is handled by manage.py shell

from league.models import League, Team, Match, Division

try:
    league_id = 421
    league = League.objects.get(pk=league_id)
    print(f"League 421 Found: {league.title}")
    
    divisions = league.divisions.all()
    print(f"Divisions count: {divisions.count()}")
    for d in divisions:
        print(f"  - Division: {d.name} (ID: {d.id})")
        teams = Team.objects.filter(league=league, division=d)
        print(f"    Teams count: {teams.count()}")
        for t in teams:
            print(f"      - {t.name} (ID: {t.id})")

    if divisions.count() == 0:
        teams = Team.objects.filter(league=league)
        print(f"Teams count (No divisions): {teams.count()}")
        for t in teams:
            print(f"  - {t.name} (ID: {t.id})")

    matches = Match.objects.filter(round__league=league)
    print(f"Matches count: {matches.count()}")
    
    completed_matches = matches.filter(status='Completed')
    # Checking status field type in model would be good, but assuming string 'COMPLETED' or similar constant based on previous context.
    # Actually, previous code used `MATCH_STATUS_COMPLETED` variable. I'll inspect models to be sure or just print all matches status.
    print(f"Completed matches count: {completed_matches.count()}")

except League.DoesNotExist:
    print(f"League {league_id} does not exist.")
except Exception as e:
    print(f"Error: {e}")
