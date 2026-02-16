import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nycs.settings')
django.setup()

from league.models import WebsiteIncludeText
from django.contrib.flatpages.models import FlatPage
from league.models import League, Venue

print('--- WebsiteIncludeText ---')
for t in WebsiteIncludeText.objects.all():
    print(f'ID: {t.id} | Name: "{t.name}" | Slug: "{django.utils.text.slugify(t.name)}"')
    print(f'Text: {t.text[:200]}...')
    print('-' * 20)

print('\n--- FlatPages ---')
for f in FlatPage.objects.all():
    print(f'URL: {f.url} | Title: {f.title}')

print('\n--- Active Leagues (STATUS_RECRUIT) ---')
from league.models import STATUS_RECRUIT
leagues = League.objects.filter(status=STATUS_RECRUIT)
print(f'Found {leagues.count()} leagues recruiting.')
for l in leagues:
    print(f'ID: {l.id} | Name: {l.name} | Location: {l.location.location} | Image: {l.location.image}')
