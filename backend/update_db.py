import psycopg2

conn = psycopg2.connect(
    dbname="evogo_users",
    user="postgres",
    password="postgres",
    host="db"
)
cur = conn.cursor()
cur.execute("UPDATE instances SET webhook = 'http://backend:8000/api/v1/webhooks/evolution', events = 'MESSAGES_UPSERT,CONNECTION_UPDATE,MESSAGE_UPSERT,MESSAGE';")
conn.commit()
cur.close()
conn.close()
print("Updated database")
