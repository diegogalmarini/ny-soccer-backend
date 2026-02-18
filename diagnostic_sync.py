from league.models import League, STATUS_DISABLED, STATUS_FINISHED

print("--- Looking for old leagues (2017) that are still 'active' ---")
old_leagues = League.objects.exclude(status__in=[STATUS_DISABLED, STATUS_FINISHED]).filter(name__icontains='2017')
for l in old_leagues:
    print(f"ID: {l.id} | Name: {l.name} | Status: {l.status} | Location: {l.location.location if l.location else 'None'}")

print("\n--- Looking for Williamsburg 2025/26 misaligned league ---")
w_leagues = League.objects.filter(name__icontains='WILLIAMSBURG Winter 2025/26')
for l in w_leagues:
    print(f"ID: {l.id} | Name: {l.name} | Status: {l.status} | Location: {l.location.location if l.location else 'None'}")

print("\n--- Listing all Venues ---")
from league.models import Venue
for v in Venue.objects.all():
    print(f"ID: {v.id} | Location: {v.location} | Address: {v.address}")
