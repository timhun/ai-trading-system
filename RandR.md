# AI Agent 角色分工 (R&R)

# 版本：v1.0 | 最後更新：2025-10-26

角色與責任 (R&R) - 6 Agent 完整分工 (v2.0)

| Agent | 角色 | 職責 | 模型 | 環境 | 輸出 |
|-------|------|------|------|------|------|
| **A1** | **Market_Analyst** | 技術指標 + LLM 解釋 + 全天候觀察報告 | `gpt-oss:20b` (本地) | `PC + Ollama` | `reports/daily_signal_log.md` + `.png` |
| **A2** | **Macro_Analyst** | FRED 宏觀 z-score + 產業鏈關聯 | 純 Python + `Groq` (免費) | `PC + .env` | `macro_YYYYMMDD.json` |
| **A3** | **Risk_Controller** | VaR / Kelly / 止損 / 部位控管 | 純 Python | `PC + WSL` | `risk_YYYYMMDD.json` |
| **A4** | **Strategy_Executor** | 模擬下單 + 記錄 + Alpaca 整合 | 純 Python | `PC + Docker` | `reports/trade_log.md` |
| **A5** | **Performance_Reporter** | 報表 + 權益曲線 + 多渠道發送 | `matplotlib` + `python-telegram-bot` | `PC + Ollama` | `reports/daily_report.md` + Telegram/Slack/Email |
| **A6** | **Model_Tuner** | LoRA 微調 + LLM 決策層 | `Gemini-1.5-pro` (雲端) | `PC + GPU` | `adapter/` + 最終建議 |

## LLM 分層調用策略（優化版）

| 層級 | 模型 | 任務 | 觸發條件 | 成本 |
|------|------|------|----------|------|
| **L1** | `gpt-oss:20b` | 新聞過濾、關鍵字提取、模板填充 | 每日自動 | 0 |
| **L2** | `Groq` | 快速摘要、技術說明 | L1 後 | 0 |
| **L3** | `Gemini-1.5-pro` | 決策建議、風險評估 | **僅有信號或重大事件** | 低 |

## 外部角色
| 角色 | 責任 |
|------|------|
| **您** | 提供 API Key、驗收、決策 |
| **Grok** | 程式碼生成、除錯、文件更新 |
| **Windmill** | 雲端排程執行（Phase 9） |
| **Alpaca** | 模擬盤交易 API |

## 明日作業流程
1. 您提供：`Groq API Key`、`Gemini API Key`、`Windmill 帳號`
2. Grok 部署 Windmill 工作流
3. 測試 `--report` 雲端自動執行

