import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    def __init__(self, config, use_db=False):
        self.config = config
        self.window = config["momentum"]["window"]
        self.hold_days = config["momentum"]["hold_days"]
        self.symbols = config["symbols"]
        self.use_db = use_db

    def download_data(self, start, end):
        if self.use_db:
            from scripts.db_loader import DBLoader
            loader = DBLoader()
            prices = loader.load_from_db(self.symbols, start, end)
            if prices is not None and not prices.empty:
                print("Momentum: 從 PostgreSQL 載入資料")
                # 確保 DB 載入的索引是 DatetimeIndex
                prices.index = pd.to_datetime(prices.index)
                return prices
            print("Momentum: DB 無資料，切換 yfinance")
            
        import yfinance as yf
        closes = []
        for s in self.symbols:
            df = yf.download(s, start=start, end=end, progress=False, auto_adjust=False)
            if df.empty or 'Close' not in df.columns:
                continue
                
            # ***** 保持您之前的關鍵修正：扁平化 MultiIndex *****
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            # **********************************************
                
            close_series = df['Close']
            close_series.name = s
            closes.append(close_series)
            
        return pd.concat(closes, axis=1).dropna()

    def generate_signals(self, prices):
        # 計算持倉期回報
        returns = prices.pct_change(self.hold_days)
        # 計算 rolling 動量
        momentum = returns.rolling(self.window).mean()
        # 依據動量排名 (ascending=False: 動量越大，排名越靠前 (1))
        rank = momentum.rank(axis=1, ascending=False)
        
        signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        
        # ***** 排名邏輯修正：確保只選取 Top 1 和 Bottom 1 *****
        signals[rank == 1] = 1  # 動量最強 (排名 1) -> 買入 (1)
        signals[rank == len(self.symbols)] = -1 # 動量最弱 (排名最後) -> 賣空 (-1)
        
        return signals

    def backtest(self, config=None):
        # ... (backtest 方法保持不變) ...
        config = config or self.config
        start = config["start_date"]
        end = config["end_date"]
        
        prices = self.download_data(start, end)
        if prices.empty:
            print("回測失敗: 無有效的價格數據。")
            return {"total_return": 0, "max_drawdown": 0, "sharpe": 0, "cum_ret": pd.Series(1, index=[start])}

        signals = self.generate_signals(prices)
        daily_ret = prices.pct_change()
        # 信號延遲一天 (shift(1))，以避免未來函數
        strategy_ret = (signals.shift(1) * daily_ret).mean(axis=1)
        cum_ret = (1 + strategy_ret).cumprod()
        
        total = cum_ret.iloc[-1] - 1
        mdd = (cum_ret / cum_ret.cummax() - 1).min()
        sharpe = strategy_ret.mean() / strategy_ret.std() * np.sqrt(252) if strategy_ret.std() != 0 else 0
        
        plt.figure(figsize=(12,6))
        cum_ret.plot()
        plt.title(f"Momentum (DB: {self.use_db}) Return: {total:.2%}, MDD: {mdd:.2%}, Sharpe: {sharpe:.2f}")
        plt.savefig("reports/phase5_momentum_db_curve.png")
        plt.close()
        
        return {"total_return": total, "max_drawdown": mdd, "sharpe": sharpe, "cum_ret": cum_ret}