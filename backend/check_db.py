import psycopg2

conn = psycopg2.connect(
    dbname="evogo_users",
    user="postgres",
    password="postgres",
    host="db"
)
cur = conn.cursor()
cur.execute("SELECT * FROM instances;")
colnames = [desc[0] for desc in cur.description]
rows = cur.fetchall()
for row in rows:
    print(dict(zip(colnames, row)))
cur.close()
conn.close()
