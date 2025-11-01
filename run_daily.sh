#!/bin/bash
# ================================================
# AI 投資 Podcast - 自動化每日執行腳本
# 適用環境: Ubuntu (WSL) / GitHub Actions
# ================================================

set -e
cd /mnt/c/DEV/ai-podcast-system

echo "📅 $(date '+%Y-%m-%d %H:%M:%S') — 開始自動產出流程"

# 1️⃣ 啟用虛擬環境
source podcast-env/bin/activate

# 2️⃣ 載入環境變數
export $(grep -v '^#' .env | xargs)
export PYTHONPATH=$(pwd)

# 3️⃣ 順序執行主要模組
python -m src.collector
python -m src.analyze_strategy_ollama
python -m src.pk_engine
python -m src.generate_script
python -m src.tts_publish
python -m src.publish_bot

echo "✅ Pipeline 全部完成！$(date '+%Y-%m-%d %H:%M:%S')"
