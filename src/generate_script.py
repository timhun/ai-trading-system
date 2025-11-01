import os, json
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from src.progress import append_block

load_dotenv()

# === Import all possible providers ===
from openai import OpenAI
import google.generativeai as genai
from groq import Groq

# Initialize clients
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def fetch_winners():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT style, symbol_tested, total_return_pct, max_drawdown_pct, win_rate_pct, summary_for_host
        FROM pk_result
        WHERE rank_in_style = 1
        ORDER BY backtested_at DESC
        LIMIT 2;
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------- STRATEGIST ----------
def strategist_comment(record):
    style, symbol, tr, mdd, wr, summary = record
    prompt = f"""你是一位資深投資顧問，請根據以下策略回測結果撰寫一段專業分析：
策略類型：{style}
標的：{symbol}
報酬率：{tr:.2f}%
最大回撤：{mdd:.2f}%
勝率：{wr or 'n/a'}%
摘要：{summary}
"""
    # try OpenAI first
    try:
        resp = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        err = str(e)
        print(f"⚠️ OpenAI 失敗，原因：{err[:80]}")

    # fallback to Groq
    try:
        resp = client_groq.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq 失敗：{str(e)[:80]}")

    # fallback to Gemini
    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini 失敗：{str(e)[:80]}")

    return "⚠️ 無法生成策略分析：所有模型皆失敗"

# ---------- NARRATOR ----------
def narrator_script(analysis):
    prompt = f"""你是Podcast主持人，請根據以下分析撰寫一份可唸的講稿與Markdown報告：
---
{analysis}
---
請輸出：
# 講稿逐字稿
（約700字，口語化、自然）
# Markdown 投資報告
（條列摘要 + 指標表格 + 免責聲明）
"""

    # 同樣優先順序
    for provider in ["openai", "groq", "gemini"]:
        try:
            if provider == "openai":
                resp = client_openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
                return resp.choices[0].message.content.strip()
            elif provider == "groq":
                resp = client_groq.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.choices[0].message.content.strip()
            elif provider == "gemini":
                model = genai.GenerativeModel("gemini-2.5-pro")
                resp = model.generate_content(prompt)
                return resp.text.strip()
        except Exception as e:
            print(f"⚠️ {provider.upper()} 失敗：{str(e)[:80]}")
            continue

    return "⚠️ 所有模型均失敗，無法生成講稿"

# ---------- MAIN ----------
def main():
    records = fetch_winners()
    if not records:
        print("⚠️ 沒有找到冠軍策略")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("outputs", exist_ok=True)
    logs = []

    for rec in records:
        style, symbol, tr, mdd, wr, summary = rec
        print(f"🎯 生成 {style} ({symbol}) 講稿中...")
        analysis = strategist_comment(rec)
        script = narrator_script(analysis)

        md_path = f"outputs/episode_{today}_{style}.md"
        txt_path = f"outputs/episode_{today}_{style}_script.txt"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(script)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(script)

        msg = f"✅ {style} 策略講稿完成 → {md_path}"
        print(msg)
        logs.append(msg)

    append_block("Strategist & Narrator Agent", logs)
    print("📝  已更新 logs/progress.md")

if __name__ == "__main__":
    main()
