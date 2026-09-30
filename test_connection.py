import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="finance_tracker",
    user="postgres",
    password="Tuhin@2008",
    port="5432"
)

cur = conn.cursor()
cur.execute("SELECT * FROM categories;")
rows = cur.fetchall()

for row in rows:
    print(row)

cur.close()
conn.close()