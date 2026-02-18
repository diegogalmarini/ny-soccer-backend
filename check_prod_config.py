import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nycs.settings')
try:
    django.setup()
    print("Django setup successful")
    print(f"BASE_DIR: {settings.BASE_DIR}")
    print(f"SITE_ID: {settings.SITE_ID}")
    
    from django.db import connections
    conn = connections['default']
    conn.cursor()
    print("Database connection successful")
    
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    print(f"Current site: {site.domain} (id={site.id})")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
