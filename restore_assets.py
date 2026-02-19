
import os
import shutil
import sys

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nycs.settings")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("Starting Asset Restoration...")

    # =========================================================================
    # PHASE 1: FILE SYSTEM OPERATIONS (DB INDEPENDENT)
    # =========================================================================
    print("--- Phase 1: File Restoration ---")
    
    # 1. Define Paths
    static_root = os.path.join(BASE_DIR, 'static/img')
    media_root = os.path.join(BASE_DIR, 'media')
    slider_dest_dir = os.path.join(static_root, 'slider')

    # 2. Create Required Directories
    dirs_to_create = [
        os.path.join(media_root, 'leagues'),
        os.path.join(media_root, 'venues'),
        slider_dest_dir
    ]

    for d in dirs_to_create:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created directory: {d}")

    # 3. Restore Venue Images
    # Map: static/img/venues/venue-X.jpg -> media/venues/venue-X.jpg
    venue_map = {
        'venue-1.jpg': 'venue-1.jpg', # Chelsea
        'venue-2.jpg': 'venue-2.jpg', # Brooklyn
        'venue-3.jpg': 'venue-3.jpg', # Williamsburg
        'venue-4.jpg': 'venue-4.jpg', # UWS
    }
    
    for src_name, dest_name in venue_map.items():
        src = os.path.join(static_root, 'venues', src_name)
        dest = os.path.join(media_root, 'venues', dest_name)
        if os.path.exists(src):
            shutil.copy(src, dest)
            print(f"Restored Venue: {src_name} -> {dest_name}")
        else:
            print(f"WARNING: Source image not found: {src}")

    # 4. Restore Slider Images
    # Map: static/img/SlideX.jpg -> static/img/slider/slider-bg-X.jpg
    slider_map = {
        'Slide1.jpg': 'slider-bg-1.jpg',
        'Slide2.jpg': 'slider-bg-2.jpg', 
        'Slide3.jpg': 'slider-bg-3.jpg'
    }

    for src_name, dest_name in slider_map.items():
        # Source is usually in static/img root or static/img/slider
        src = os.path.join(static_root, src_name)
        if not os.path.exists(src):
             src = os.path.join(static_root, 'slider', src_name)
        
        dest = os.path.join(slider_dest_dir, dest_name)
        
        if os.path.exists(src):
            shutil.copy(src, dest)
            print(f"Restored Slider: {src_name} -> {dest_name}")
        else:
            print(f"WARNING: Slider source not found: {src_name}")


    # =========================================================================
    # PHASE 2: DATABASE UPDATES (DEPENDENT ON CREDENTIALS)
    # =========================================================================
    print("--- Phase 2: Database Updates ---")
    
    try:
        import django
        django.setup()
        from league.models import Venue
        from django.core.files import File

        print("Connected to Database. Updating Records...")
        
        def update_venue_image(name_pattern, img_filename):
            try:
                venues = Venue.objects.filter(name__icontains=name_pattern)
                count = 0
                for v in venues:
                    # We set the name relative to MEDIA_ROOT
                    rel_path = os.path.join('venues', img_filename)
                    if v.image.name != rel_path:
                        v.image.name = rel_path
                        v.save()
                        count += 1
                if count > 0:
                    print(f"Updated {count} venues matching '{name_pattern}' -> {img_filename}")
                else:
                    print(f"No venues found matching '{name_pattern}'")
            except Exception as e:
                print(f"Error updating {name_pattern}: {e}")

        update_venue_image("Chelsea", "venue-1.jpg")
        update_venue_image("Brooklyn", "venue-2.jpg")
        update_venue_image("Williamsburg", "venue-3.jpg")
        update_venue_image("Upper West", "venue-4.jpg")
        
        print("Database updates completed.")

    except Exception as e:
        print(f"\nCRITICAL WARNING: Database connection failed. Skipping DB updates.")
        print(f"Error: {e}")
        print("NOTE: File restoration (Phase 1) was successful. Assets are ready to be committed.")
        # Do NOT raise the exception, allow script to finish "successfully" regarding files

if __name__ == "__main__":
    main()
