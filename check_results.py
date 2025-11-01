import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== 分析結果 ===")
cur.execute("""
    SELECT 
        c.source_id,
        c.title,
        s.is_strategy,
        s.style,
        LEFT(s.core_claim, 50) as claim
    FROM candidate_strategy s
    JOIN raw_content c ON s.raw_content_id = c.id
    WHERE c.source_id LIKE 'test_%'
    ORDER BY c.source_id
""")

rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"\n{row[0]} - {row[1]}:")
        print(f"  是策略: {row[2]}")
        print(f"  類型: {row[3]}")
        print(f"  主張: {row[4]}")
else:
    print("  (無結果)")

conn.close()
