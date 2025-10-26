import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

symbols = ["QQQ", "NVDA", "TSLA", "AAPL", "MSFT"]
closes = []

print("正在下載 2023 年資料...")
for s in symbols:
    df = yf.download(s, start="2023-01-01", end="2023-12-31", progress=False)
    close_series = df['Close']
    close_series.name = s  # 正確設定 Series 名稱
    closes.append(close_series)
    print(f"  {s}: {len(df)} 筆")

portfolio = pd.concat(closes, axis=1).dropna()
zscore = (portfolio.mean(axis=1) - portfolio.mean(axis=1).rolling(20).mean()) / portfolio.mean(axis=1).rolling(20).std()

signals = pd.DataFrame(0, index=portfolio.index, columns=portfolio.columns)
signals[zscore > 2.0] = -1
signals[zscore < -2.0] = 1

ret = portfolio.pct_change()
strategy_ret = (signals.shift(1) * ret).mean(axis=1)
cum = (1 + strategy_ret).cumprod()

total = cum.iloc[-1] - 1
mdd = (cum / cum.cummax() - 1).min()

plt.figure(figsize=(12,6))
cum.plot(title=f"Phase 2 Mean Reversion (Return: {total:.2%}, MDD: {mdd:.2%})")
plt.savefig("reports/phase2_equity_curve.png")
plt.close()

print(f"\n總報酬: {total:.2%}")
print(f"最大回撤: {mdd:.2%}")
print("Phase 2 完成 ✅")