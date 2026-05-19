import psycopg2
import os

def check_db(dbname):
    print(f"\nChecking database: {dbname}")
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user="postgres",
            password="postgres_pass_change_me",
            host="localhost" # Since I'm outside docker but maybe it's mapped? 
                             # Wait, .env says host=db. 
                             # If I'm on the host machine, I should try localhost or check docker mapping.
        )
        cur = conn.cursor()
        if dbname == "whatsapp_saas":
            cur.execute("SELECT instance_name FROM tickets_connection;")
        elif dbname == "evogo_users":
            cur.execute("SELECT name FROM instances;")
        
        rows = cur.fetchall()
        for row in rows:
            print(f" - {row[0]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error checking {dbname}: {e}")

# Try with localhost first
check_db("whatsapp_saas")
check_db("evogo_users")
