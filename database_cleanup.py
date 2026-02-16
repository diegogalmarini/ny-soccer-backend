import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nycs.settings')
django.setup()

from league.models import WebsiteIncludeText, League
from django.contrib.flatpages.models import FlatPage

def clean_content(model, field_name):
    print(f"Cleaning {model.__name__}.{field_name}...")
    items = model.objects.all()
    count = 0
    for item in items:
        val = getattr(item, field_name)
        if val:
            new_val = val.replace('\\r\\n', '\n').replace('\\n', '\n')
            if new_val != val:
                setattr(item, field_name, new_val)
                item.save()
                count += 1
    print(f"Updated {count} records in {model.__name__}.")

if __name__ == "__main__":
    clean_content(WebsiteIncludeText, 'text')
    clean_content(FlatPage, 'content')
    clean_content(League, 'league_description')
    clean_content(League, 'game_location')

