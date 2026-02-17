# Django setup is handled by manage.py shell

from league.models import League

# Expected mapping from batch_10.sql
# Format: {LegacyID: "Legacy Name"}
legacy_leagues = {
    395: 'Tuesday BROOKLYN BRIDGE PARK Summer 2025 Outdoor 9s',
    397: 'BROOKLYN BRIDGE PARK Fall 2025 Outdoor 9s',
    398: 'GANSEVOORT Fall 2025 Outdoor 7s',
    399: 'MIDTOWN WEST - DeWitt Clinton Fall 2025 Outdoor 7s',
    401: 'LOWER EAST SIDE Fall 2025 Outdoor 7s',
    402: 'WILLIAMSBURG Fall 2025 Outdoor 7s',
    403: 'BROOKLYN BRIDGE PARK Fall 2025 Outdoor 9s [D]',
    404: 'WILLIAMSBURG Winter 2025/26 Outdoor 7s',
    405: 'WILLIAMSBURG Winter 2025/26 Outdoor 7s', # Note: Duplicate name in audit, check detail if possible
    408: 'BROOKLYN BRIDGE PARK Spring 2026 Outdoor 9s',
    409: 'CHELSEA Spring 2026 Outdoor 7s',
    410: 'LOWER EAST SIDE Spring 2026 Outdoor 7s',
    411: 'WILLIAMSBURG Spring 2026 Outdoor 7s'
}

# Fetch all leagues from DB
db_leagues = League.objects.all().order_by('id')

print("-- Legacy ID Mapping Plan --")
print("-- Current State:")

# Helper to normalize names for comparison
def normalize(name):
    return name.lower().replace(' ', '').replace('outdoor', '').replace('7s', '').replace('9s', '').replace('5s', '').replace('indoor', '').replace('tuesday', '').replace('thursday', '').replace('friday', '').replace('monday', '').replace('sunday', '').replace('wednesday', '').replace('midtownwest-', '').replace('dewittclinton', 'midtownwest').replace('les', 'lowereastside')

mapped_ids = {}
conflicts = []

for legacy_id, legacy_name in legacy_leagues.items():
    found = False
    legacy_norm = normalize(legacy_name)
    
    # Try exact match first
    for league in db_leagues:
        if league.name == legacy_name:
            print(f"-- Exact match: {legacy_id} -> {league.id} ({league.name})")
            mapped_ids[legacy_id] = league.id
            found = True
            break
    
    # Try fuzzy/normalized match
    if not found:
        candidates = []
        for league in db_leagues:
            db_norm = normalize(league.name)
            if legacy_norm in db_norm or db_norm in legacy_norm:
                # Check for year/season match to avoid cross-season mapping
                if '2025' in legacy_name and '2025' not in league.name: continue
                if '2026' in legacy_name and '2026' not in league.name: continue
                if 'Fall' in legacy_name and 'Fall' not in league.name: continue
                if 'Spring' in legacy_name and 'Spring' not in league.name: continue
                if 'Summer' in legacy_name and 'Summer' not in league.name: continue
                if 'Winter' in legacy_name and 'Winter' not in league.name: continue
                
                candidates.append(league)
        
        if len(candidates) == 1:
            league = candidates[0]
            print(f"-- Fuzzy match: {legacy_id} -> {league.id} ({league.name}) [Legacy: {legacy_name}]")
            mapped_ids[legacy_id] = league.id
        elif len(candidates) > 1:
            print(f"-- Ambiguous match for {legacy_id} ({legacy_name}): {[l.name for l in candidates]}")
        else:
            print(f"-- NO MATCH FOUND for {legacy_id} ({legacy_name})")

print("\n-- Migration SQL Preview --")
print("BEGIN;")

# Generate moves
# 1. Move existing IDs out of the way if they are occupying a target LegacyID but are NOT that legacy league
# 2. Move mapped leagues to their LegacyID

# identify occupants
occupants = {}
for league in db_leagues:
    occupants[league.id] = league
    
# Plan moves
moves = []

# First pass: identify verified mappings
for legacy_id, db_id in mapped_ids.items():
    if legacy_id != db_id:
        # We need to move db_id to legacy_id
        # Check if legacy_id is occupied
        if legacy_id in occupants:
            occupant = occupants[legacy_id]
            # Is this occupant the one we want to be here? 
            # If mapped_ids[legacy_id] == occupant.id (which is legacy_id), then yes.
            # But here db_id != legacy_id, so the occupant is DIFFERENT.
            # We must evict the occupant.
            print(f"-- Conflict: Target {legacy_id} is occupied by {occupant.name} (ID {occupant.id}). Will move occupant to {occupant.id + 10000} first.")
            moves.append((occupant.id, occupant.id + 10000))
            occupants[occupant.id + 10000] = occupant
            del occupants[legacy_id]
            
        # Now move the source
        moves.append((db_id, legacy_id))
        occupants[legacy_id] = occupants[db_id]
        if db_id in occupants: del occupants[db_id]

# Print SQL
# Use a constraint handling approach or temporary IDs
for old_id, new_id in moves:
    print(f"UPDATE league_league SET id = {new_id} WHERE id = {old_id};")

print("COMMIT;")
