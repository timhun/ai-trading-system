import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== raw_content 資料表欄位 ===")
cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name='raw_content' 
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    nullable = "NULL" if row[2] == "YES" else "NOT NULL"
    print(f"  {row[0]:20} {row[1]:20} {nullable}")

conn.close()
