import os
from datetime import datetime

# 決定正確的 logs 目錄位置（不論目前在哪個資料夾執行）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

PROGRESS_FILE = os.path.join(LOG_DIR, "progress.md")

def append_block(title: str, lines: list[str]):
    """將進度紀錄追加至 logs/progress.md"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = [f"## {timestamp} — {title}\n"]
    for line in lines:
        block.append(f"- {line}")
    block.append("\n")

    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(block))

    print(f"📝  已更新 {PROGRESS_FILE} → {len(lines)} 筆紀錄")

# 若要從 CLI 測試：
if __name__ == "__main__":
    append_block("Test Agent", ["✅ 寫入測試成功", "⚙️  自動判定路徑成功"])
