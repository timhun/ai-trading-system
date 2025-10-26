import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    def __init__(self, config):
        self.config = config
        self.window = config["momentum"]["window"]
        self.hold_days = config["momentum"]["hold_days"]
        self.symbols = config["symbols"]

    def download_data(self, start, end):
        import yfinance as yf
        closes = []
        for s in self.symbols:
            df = yf.download(s, start=start, end=end, progress=False)
            close_series = df['Close']
            close_series.name = s
            closes.append(close_series)
        return pd.concat(closes, axis=1).dropna()

    def generate_signals(self, prices):
        returns = prices.pct_change(self.hold_days)
        momentum = returns.rolling(self.window).mean()
        rank = momentum.rank(axis=1, ascending=False)
        signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        signals[rank <= 1] = 1  # 買入動能最強
        signals[rank >= len(self.symbols)] = -1  # 賣空最弱
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
        sharpe = strategy_ret.mean() / strategy_ret.std() * np.sqrt(252)

        plt.figure(figsize=(12,6))
        cum_ret.plot()
        plt.title(f"Momentum (Return: {total:.2%}, MDD: {mdd:.2%}, Sharpe: {sharpe:.2f})")
        plt.savefig("reports/phase4_momentum_curve.png")
        plt.close()

        return {"total_return": total, "max_drawdown": mdd, "sharpe": sharpe, "cum_ret": cum_ret}
