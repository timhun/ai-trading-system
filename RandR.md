# AI Agent 角色分工 (R&R)

# 版本：v1.0 | 最後更新：2025-10-26

---

## 6 個 AI Agent 完整分工

| Agent | 角色 | 職責 | 模型 | 環境 | 輸出 |
| --- | --- | --- | --- | --- | --- |
| **A1** | Market_Analyst | 技術指標 + LLM 解釋 | `mistral:7b` / `gpt-oss:120b` | `PC + Ollama` | `signals_YYYYMMDD.json` |
| **A2** | Macro_Analyst | FRED 宏觀 z-score | 純 Python | `NB + .env` | `macro_YYYYMMDD.json` |
| **A3** | Risk_Controller | VaR / Kelly / 止損 | 純 Python | `PC + WSL` | `risk_YYYYMMDD.json` |
| **A4** | Strategy_Executor | 模擬下單 + 記錄 | 純 Python | `NB + Docker` | `portfolio.csv` |
| **A5** | Performance_Reporter | 報表 + 權益曲線 | `matplotlib` | `PC + Ollama` | `report_YYYYMMDD.md` + `.png` |
| **A6** | Model_Tuner | LoRA 微調 | `peft` | `PC + GPU` | `adapter/` |

---

## 每日協同流程

```
21:00 cron (NB) → A2 → A1 → A3 → A4 → A5 → GitHub PR
```

## 迭代加速

- PR 自動標籤：agent/A1
- 失敗重試：retry_queue.json
- A/B 測試：並行回測

# 角色與責任 (R&R)

| 角色 | 責任 |
|------|------|
| **您** | 提供需求、API Key、驗收 |
| **Grok** | 程式碼生成、除錯、文件更新 |
| **A1 Agent** | 智能分析與解釋 |
| **Windmill** | 雲端排程執行 |
| **Alpaca** | 模擬盤交易 |

## 明日作業流程
1. 您提供：`Groq API Key`、`Gemini API Key`、`Windmill 帳號`
2. Grok 部署 Windmill 工作流
3. 測試 `--report` 雲端自動執行

