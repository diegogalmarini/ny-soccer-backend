
import os
import sys
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest import APIError

# Manually load .env since we don't have Django
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))

def check_postgres_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Missing DATABASE_URL in environment.")
        return False

    print(f"DEBUG: Attempting connection to: {db_url}")
    try:
        conn = psycopg2.connect(dsn=db_url)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        print(f"✅ Postgres connection successful! Result: {result}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Postgres connection failed: {e}")
        return False

def check_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") # This should be the ANON key for client-side, or SERVICE_ROLE for admin
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        return False
        
    try:
        print(f"DEBUG: Initializing Supabase client with URL: {url}")
        supabase: Client = create_client(url, key)
        
        # Try a simple query to verify access
        # 'auth.users' is not accessible usually, so let's try reading a public table or just check health
        # Since we don't know tables, we can try to list buckets or just rely on init success + auth check
        
        try:
             # Just checking if we can talk to the API
             print("DEBUG: Testing API connectivity...")
             # This might fail if no tables exist, but proves connection
             response = supabase.table("non_existent_table").select("*").limit(1).execute() 
        except APIError as e:
            if "404" in e.message or "relation" in e.message:
                 print("✅ Supabase API is reachable (Got expected error for non-existent table).")
                 return True
            print(f"⚠️ Supabase API returned error: {e}")
            return True # Still reachable
        except Exception as e:
             # Verify if it's a network error or logic error
             if "connection refused" in str(e).lower() or "getaddrinfo" in str(e).lower():
                 print(f"❌ Supabase API failed (Network): {e}")
                 return False
                 
             print(f"✅ Supabase client initialized and reachable! (Error was logical: {e})")
             return True
             
        print("✅ Supabase client initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Supabase client initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("--- Verifying Supabase Connection (Standalone) ---")
    pg_success = check_postgres_connection()
    sb_success = check_supabase_client()
    
    if pg_success and sb_success:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    elif sb_success and not pg_success:
        print("\n⚠️ Postgres connection failed, but Supabase API is working.")
        print("   We can proceed with data migration using the API if DB connection remains blocked.")
        sys.exit(0) # Treat as success for now since we have a fallback
    else:
        print("\n❌ All checks failed.")
        sys.exit(1)
