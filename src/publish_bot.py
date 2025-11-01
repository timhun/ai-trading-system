import os
import datetime
import glob
import xml.etree.ElementTree as ET
from src.progress import append_block

# -----------------------------------------------------
# ⚙️ 基本設定
# -----------------------------------------------------
OUTPUT_DIR = "outputs/audio"
PUBLIC_DIR = "public"
RSS_FILE = os.path.join(PUBLIC_DIR, "feed.xml")

SITE_URL = os.getenv("SITE_URL", "https://timhun.github.io/ai-trading-system")
PODCAST_TITLE = "AI 投資 Podcast"
PODCAST_DESC = "每日由 AI 自動生成的投資策略與市場觀察"
PODCAST_AUTHOR = "AI 投資系統"

# -----------------------------------------------------
# 🧠 RSS Feed 生成
# -----------------------------------------------------
def build_rss_feed(episodes):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = PODCAST_TITLE
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = PODCAST_DESC
    ET.SubElement(channel, "language").text = "zh-TW"

    for ep in episodes:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = ep["title"]
        ET.SubElement(item, "description").text = ep["desc"]
        ET.SubElement(item, "link").text = ep["url"]
        ET.SubElement(item, "guid").text = ep["url"]
        ET.SubElement(item, "pubDate").text = ep["date"]
        ET.SubElement(item, "enclosure", attrib={
            "url": ep["url"],
            "type": "audio/mpeg"
        })

    tree = ET.ElementTree(rss)
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅ RSS feed 已生成：{RSS_FILE}")

# -----------------------------------------------------
# 🪶 自動 git commit + push
# -----------------------------------------------------
def git_push():
    repo = os.getenv("GITHUB_REPO")
    token = os.getenv("GITHUB_TOKEN")

    if not repo or not token:
        print("⚠️ 未設定 GITHUB_REPO 或 GITHUB_TOKEN，略過自動上傳")
        return

    print("📤 準備推送至 GitHub Pages...")
    os.system("git add public/* logs/progress.md || true")
    os.system('git commit -m "📢 Auto publish new podcast episode" || echo "No changes to commit."')

    remote_url = f"https://{token}@github.com/{repo}.git"
    os.system(f"git push {remote_url} main")

    print(f"✅ 已自動推送到 GitHub Pages ({repo})")

# -----------------------------------------------------
# 🚀 主程序
# -----------------------------------------------------
def main():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    audio_files = sorted(glob.glob(f"{OUTPUT_DIR}/episode_*.mp3"))

    if not audio_files:
        print("⚠️ 沒有找到任何 MP3 音檔")
        return

    episodes = []
    for f in audio_files:
        filename = os.path.basename(f)
        file_date = filename.split("_")[1]
        public_path = os.path.join(PUBLIC_DIR, filename)

        os.system(f"cp '{f}' '{public_path}'")
        ep = {
            "title": f"AI 投資 Podcast {file_date}",
            "desc": f"{PODCAST_TITLE} 節目 {file_date}",
            "url": f"{SITE_URL}/{filename}",
            "date": datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
        }
        episodes.append(ep)

    build_rss_feed(episodes)

    append_block("Publish Bot (GitHub Pages)", [
        f"✅ 已發布 {len(episodes)} 集音檔至 GitHub Pages",
        f"RSS Feed: {RSS_FILE}"
    ])

    git_push()
    print("🎉 Publish Bot 完成！請稍等幾分鐘確認 GitHub Pages 已更新。")

if __name__ == "__main__":
    main()
