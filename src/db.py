import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Check your .env")
def get_conn():
    return psycopg2.connect(DATABASE_URL)
def insert_raw_content(conn, row: dict):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO raw_content (source_id, published_at, title, raw_text, url, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (row["source_id"], row["published_at"], row["title"],
              row.get("raw_text"), row.get("url"), Json(row.get("metadata", {}))))
        rid = cur.fetchone()["id"]
        conn.commit()
        return rid
