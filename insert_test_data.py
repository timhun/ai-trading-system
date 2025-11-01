import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# 清除舊的測試資料
cur.execute("DELETE FROM raw_content WHERE source_id LIKE 'test_%'")
print("✅ 已清除舊的測試資料")

# 插入真實的投資策略範例
test_strategies = [
    {
        "source_id": "test_strategy_001",
        "title": "均線黃金交叉做多策略",
        "text": """【均線黃金交叉做多策略】

這是一個經典的技術分析策略，利用短期與長期均線的交叉來判斷進出場時機。

進場條件：
1. 5日均線向上突破20日均線（黃金交叉）
2. 突破當日成交量需放大至20日均量的1.5倍以上
3. 股價必須站在60日季線之上
4. RSI指標介於40-70之間（避免超買區）

出場條件：
1. 5日均線向下跌破20日均線（死亡交叉）
2. 停損：跌破進場價格的5%
3. 停利：獲利達15%時，分批出場50%

風險控管：
- 單一個股投入資金不超過總資金的10%
- 同時持有不超過5檔個股
- 嚴格執行停損，不凹單"""
    },
    {
        "source_id": "test_strategy_002",
        "title": "突破前高策略 - 量價配合法",
        "text": """【突破前高策略 - 量價配合法】

當股價突破近期高點時，若配合成交量放大，通常代表新一波漲勢啟動。

進場訊號：
✓ 股價突破近60個交易日的最高價
✓ 突破日成交量超過近20日平均量的2倍
✓ 突破後連續3日不跌破突破點

出場規則：
✗ 跌破突破點即停損出場
✗ 出現長上影線且收盤價位於當日最低1/3處，減碼50%
✗ 獲利20%以上，採用移動停利（回檔5%出場）

資金分配：
每次進場使用15%資金，最多同時持有3檔標的。"""
    },
    {
        "source_id": "test_strategy_003",
        "title": "價值投資選股法 - 長期持有",
        "text": """【價值投資選股法 - 長期持有】

選擇體質優良、獲利穩定的公司，在價格低估時買進並長期持有。

選股條件：
1. 連續5年 ROE > 15%
2. 負債比 < 50%
3. 自由現金流為正
4. 本益比低於產業平均
5. 殖利率 > 4%

買進時機：
- 股價淨值比 < 1.5
- 技術面出現季線支撐
- 大盤回檔時分批買進

持有策略：
→ 預計持有3-5年
→ 每季檢視財報，基本面惡化即出場
→ 股價漲至本益比 > 20 時，減碼50%

風險管理：
單一個股不超過20%資金，分散於5-8檔不同產業的優質股。"""
    },
    {
        "source_id": "test_news_001",
        "title": "今日台股盤勢分析",
        "text": """今日台股盤勢分析

台股今日開高走低，終場下跌85點，收在17,234點。
三大法人賣超120億，外資賣超100億，投信賣超15億。

類股表現：
電子股：台積電下跌1.5%，聯發科持平
金融股：國泰金上漲0.8%，富邦金下跌0.3%

市場消息：美股昨夜收黑，那斯達克指數跌1.2%。
分析師看法：短期整理格局，關注美國利率政策動向。"""
    }
]

now = datetime.now()

for item in test_strategies:
    cur.execute("""
        INSERT INTO raw_content (source_id, title, raw_text, published_at, status)
        VALUES (%s, %s, %s, %s, 'new')
    """, (item['source_id'], item['title'], item['text'], now))
    print(f"  ✓ 插入 {item['source_id']}")

conn.commit()

print("\n✅ 成功插入測試資料")
print("\n📊 驗證：")
cur.execute("""
    SELECT source_id, title, LENGTH(raw_text) as len, status 
    FROM raw_content 
    WHERE source_id LIKE 'test_%'
    ORDER BY source_id
""")
for row in cur.fetchall():
    print(f"  {row[0]}")
    print(f"    標題: {row[1]}")
    print(f"    長度: {row[2]} 字元")
    print(f"    狀態: {row[3]}")

conn.close()
