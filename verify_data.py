import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== 測試資料 ===")
cur.execute("""
    SELECT source_id, title, LENGTH(raw_text), status 
    FROM raw_content 
    WHERE source_id LIKE 'test_%'
    ORDER BY source_id
""")
for row in cur.fetchall():
    print(f"\n{row[0]}:")
    print(f"  標題: {row[1]}")
    print(f"  長度: {row[2]} 字元")
    print(f"  狀態: {row[3]}")

conn.close()
