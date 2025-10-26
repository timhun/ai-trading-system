import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.base_strategy import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, config, use_db=False):
        self.config = config
        self.window = config["mean_reversion"]["window"]
        self.threshold = config["mean_reversion"]["threshold"]
        self.symbols = config["symbols"]
        self.use_db = use_db

    def download_data(self, start, end):
        if self.use_db:
            from scripts.db_loader import DBLoader
            loader = DBLoader()
            prices = loader.load_from_db(self.symbols, start, end)
            if prices is not None and not prices.empty:
                print("MeanReversion: 從 PostgreSQL 載入資料")
                prices.index = pd.to_datetime(prices.index)
                return prices
            print("MeanReversion: DB 無資料，切換 yfinance")
        
        import yfinance as yf
        closes = []
        for s in self.symbols:
            df = yf.download(s, start=start, end=end, progress=False, auto_adjust=False)
            if df.empty or 'Close' not in df.columns:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            close_series = df['Close']
            close_series.name = s
            closes.append(close_series)
        return pd.concat(closes, axis=1).dropna()

    def generate_signals(self, prices):
        price_mean = prices.mean(axis=1)
        rolling_mean = price_mean.rolling(self.window).mean()
        rolling_std = price_mean.rolling(self.window).std()
        zscore = (price_mean - rolling_mean) / rolling_std

        signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        signals[zscore > self.threshold] = -1
        signals[zscore < -self.threshold] = 1
        return signals

    def backtest(self, config=None):
        config = config or self.config
        start = config["start_date"]
        end = config["end_date"]
        prices = self.download_data(start, end)
        signals = self.generate_signals(prices)

        daily_ret = prices.pct_change()
        strategy_ret = (signals.shift(1) * daily_ret).mean(axis=1)
        cum_ret = (1 + strategy_ret).cumprod()

        total = cum_ret.iloc[-1] - 1
        mdd = (cum_ret / cum_ret.cummax() - 1).min()

        plt.figure(figsize=(12,6))
        cum_ret.plot()
        plt.title(f"Mean Reversion (DB: {self.use_db}) Return: {total:.2%}, MDD: {mdd:.2%}")
        plt.savefig("reports/phase5_mean_reversion_db_curve.png")
        plt.close()

        return {"total_return": total, "max_drawdown": mdd}