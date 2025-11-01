import argparse, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from src.db import get_conn, insert_raw_content
from src.progress import append_block

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "config" / "sources.json"
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--date", help="YYYY-MM-DD for progress header", required=False)
    return p.parse_args()
def fetch_youtube_meta(url: str) -> dict:
    try:
        res = subprocess.run(["yt-dlp", "-J", url], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        title = data.get("title", "Untitled")
        upload_date = data.get("upload_date")  # YYYYMMDD
        pub = datetime.strptime(upload_date, "%Y%m%d") if upload_date else datetime.utcnow()
        return {"title": title, "published_at": pub, "metadata": {
            "channel": data.get("uploader"),
            "view_count": data.get("view_count"),
            "like_count": data.get("like_count"),
            "duration": data.get("duration")
        }}
    except Exception as e:
        return {"title": "Untitled", "published_at": datetime.utcnow(), "metadata": {"error": f"yt-dlp: {e}"}}
def get_youtube_id(url: str):
    if "watch?v=" in url: return url.split("watch?v=")[-1].split("&")[0]
    if "youtu.be/" in url: return url.split("youtu.be/")[-1].split("?")[0]
    return None
def fetch_youtube_transcript(url: str):
    vid = get_youtube_id(url)
    if not vid: return None
    try:
        tr = YouTubeTranscriptApi.list_transcripts(vid).find_transcript(['zh-Hant','zh-Hans','en'])
        return " ".join([e['text'] for e in tr.fetch() if e.get('text')]).strip()
    except (NoTranscriptFound, Exception):
        return None
def fetch_web_article(url: str) -> dict:
    try:
        resp = requests.get(url, timeout=20); resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.text.strip() if soup.title else "Untitled"
        article = soup.find("article")
        paras = [p.get_text(" ", strip=True) for p in (article or soup).find_all("p")]
        return {"title": title, "text": "\n".join(paras).strip()}
    except Exception as e:
        return {"title": "Untitled", "text": "", "error": str(e)}
def main():
    args = parse_args()
    today = args.date or datetime.now().strftime("%Y-%m-%d")
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    conn = get_conn()
    inserted, skipped = [], []
    for s in sorted(sources, key=lambda x: x.get("priority",0), reverse=True):
        typ, sid, url = s["type"], s["source_id"], s["url"]
        if typ == "youtube":
            meta = fetch_youtube_meta(url)
            transcript = fetch_youtube_transcript(url)
            row = {"source_id": sid, "published_at": meta["published_at"], "title": meta["title"],
                   "raw_text": transcript, "url": url, "metadata": meta.get("metadata", {})}
        elif typ == "web":
            art = fetch_web_article(url)
            row = {"source_id": sid, "published_at": datetime.utcnow(), "title": art["title"],
                   "raw_text": art.get("text"), "url": url,
                   "metadata": ({"error": art.get("error")} if art.get("error") else {})}
        else:
            skipped.append(f"⚠️ unsupported type: {sid} ({typ})"); continue
        rid = insert_raw_content(conn, row)
        inserted.append(f"✅ {sid} → raw_content.id={rid}")
    conn.close()
    lines = [f"Data Collection: {len(inserted)} inserted, {len(skipped)} skipped", *inserted, *skipped]
    append_block(today, lines)
    print("\n".join(lines))
if __name__ == "__main__":
    main()
