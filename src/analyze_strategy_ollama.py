import os, re, json, json5, psycopg2
from datetime import datetime
from dotenv import load_dotenv
from ollama import Client
from src.progress import append_block

load_dotenv()
client = Client(host="http://localhost:11434")

PROMPT = """你是一位投資策略分析師，請閱讀以下文字，僅回覆JSON，不要文字註解。
{{
  "is_strategy": true/false,
  "style": "short_term" | "long_term" | "unclear",
  "core_claim": "策略主張",
  "entry_rule": "進場條件",
  "exit_rule": "出場條件",
  "risk_control": "風險控管"
}}
文字如下：
---
{content}
---
請只輸出JSON。
"""

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def safe_parse_json(text):
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    raw = match.group(0)
    for parser in (json, json5):
        try:
            return parser.loads(raw)
        except Exception:
            continue
    return None

def analyze_text(content):
    """使用 Ollama 分析投資策略文字"""
    
    if not content or len(content.strip()) < 50:
        return None, "內容太短或為空"
    
    prompt = PROMPT.format(content=content[:2000])
    
    try:
        # 呼叫模型，關鍵修正：使用 stream=False
        resp = client.generate(
            model="gpt-oss:20B",
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.3,
                "num_predict": 800
            }
        )
        
        # 正確提取回應 - 直接使用 .response 屬性
        text = ""
        if hasattr(resp, 'response'):
            text = resp.response
        elif isinstance(resp, dict):
            text = resp.get('response', '')
        else:
            text = str(resp)
        
        if not text.strip():
            return None, f"模型回應為空"
        
        # 解析 JSON
        data = safe_parse_json(text)
        
        if not data:
            return None, f"無法解析 JSON: {text[:100]}"
        
        return data, text
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return None, f"錯誤: {str(e)}\n{error_detail[:200]}"

def main():
    conn = get_conn()
    cur = conn.cursor()
    
    # 查詢待分析資料
    cur.execute("""
        SELECT id, source_id, raw_text 
        FROM raw_content 
        WHERE status='new' 
        LIMIT 10
    """)
    rows = cur.fetchall()
    
    if not rows:
        print("⚠️ 沒有需要分析的資料（status='new'）")
        conn.close()
        return
    
    print(f"📊 找到 {len(rows)} 筆待分析資料\n")
    
    logs = []
    success_count = 0
    
    for rid, source_id, text in rows:
        short_id = str(rid)[:8]
        short_source = source_id[:30] if source_id else 'unknown'
        text_len = len(text or '')
        
        print(f"🔍 分析 {short_id} ({short_source}) - {text_len} 字元")
        
        if text_len < 50:
            logs.append(f"⏭️ {short_id} 跳過（內容太短：{text_len} 字元）")
            print(f"  ⏭️ 跳過（內容太短）\n")
            continue
        
        # 顯示內容預覽
        preview = (text or '')[:100].replace('\n', ' ')
        print(f"  📄 預覽: {preview}...")
        
        data, raw = analyze_text(text)
        
        if not data:
            logs.append(f"⚠️ {short_id} 解析失敗 - {raw[:50]}")
            print(f"  ❌ 解析失敗: {raw[:150]}\n")
            continue
        
        # 顯示解析結果
        print(f"  ✅ 解析成功:")
        print(f"     是策略: {data.get('is_strategy')}")
        print(f"     類型: {data.get('style')}")
        print(f"     主張: {data.get('core_claim', 'N/A')[:50]}")
        
        # 插入分析結果
        try:
            cur.execute("""
                INSERT INTO candidate_strategy
                (raw_content_id, is_strategy, style, core_claim, entry_rule, exit_rule,
                 risk_control, score_heat, score_recency, score_final, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'selected')
            """, (
                rid, 
                data.get("is_strategy", False), 
                data.get("style"),
                data.get("core_claim"),
                data.get("entry_rule"),
                data.get("exit_rule"),
                data.get("risk_control"),
                0.5, 0.5, 0.5
            ))
            
            cur.execute("UPDATE raw_content SET status='analyzed' WHERE id=%s", (rid,))
            
            claim_preview = data.get('core_claim', 'n/a')[:30] if data.get('core_claim') else 'n/a'
            success_msg = f"✅ {short_id} 完成 ({data.get('style')}) — {claim_preview}"
            logs.append(success_msg)
            print(f"  💾 已儲存\n")
            success_count += 1
            
        except Exception as e:
            logs.append(f"❌ {short_id} 儲存失敗: {str(e)}")
            print(f"  ❌ 儲存失敗: {e}\n")
    
    conn.commit()
    conn.close()
    
    print("="*60)
    print(f"✨ 完成！成功處理 {success_count}/{len(rows)} 筆")
    print("="*60)
    
    append_block("Analyst Agent (Ollama)", logs)
    print("\n".join(logs))

if __name__ == "__main__":
    main()