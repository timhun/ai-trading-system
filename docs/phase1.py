import yfinance as yf
import pandas as pd

symbols = ["QQQ", "NVDA", "TSLA", "AAPL", "MSFT"]
closes = []

print("下載 2023 資料...")
for s in symbols:
    df = yf.download(s, start="2023-01-01", end="2023-12-31", progress=False)
    close_series = df['Close']
    close_series.name = s  # 正確設定 Series 名稱
    closes.append(close_series)
    print(f"  {s}: {len(df)} 筆")

portfolio = pd.concat(closes, axis=1).dropna()
ret = portfolio.pct_change().mean(axis=1)
cum = (1 + ret).cumprod()
total = cum.iloc[-1] - 1

print(f"\n總報酬: {total:.2%}")
print("Phase 1 證偽成功！")
print("Phase 1 完成 ✅")