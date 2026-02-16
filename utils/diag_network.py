
import socket
import ssl
import sys

pooler_host = "aws-0-us-east-1.pooler.supabase.com"
pooler_port_session = 5432
pooler_port_transaction = 6543
direct_host = "db.gbulbdoewytbvxxmwsur.supabase.co"
direct_port = 5432

def check_socket(host, port, name):
    print(f"Testing {name} ({host}:{port})...")
    try:
        sock = socket.create_connection((host, port), timeout=5)
        print(f"✅ TCP Connection to {name} successful.")
        
        # Try SSL handshake
        context = ssl.create_default_context()
        try:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"✅ SSL Handshake with {name} successful. Version: {ssock.version()}")
        except Exception as e:
            print(f"❌ SSL Handshake with {name} failed: {e}")
            
    except Exception as e:
        print(f"❌ TCP Connection to {name} failed: {e}")

if __name__ == "__main__":
    check_socket(pooler_host, pooler_port_session, "Pooler Session (5432)")
    check_socket(pooler_host, pooler_port_transaction, "Pooler Transaction (6543)")
    check_socket(direct_host, direct_port, "Direct DB (5432)")
