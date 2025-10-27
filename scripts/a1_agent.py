import ollama
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from scripts.db_loader import DBLoader

class A1Agent:
    def __init__(self):
        with open("config/ollama.json") as f:
            config = json.load(f)
        self.client = ollama.Client(host=config["host"])
        self.model = config["model"]
        self.loader = DBLoader()
        self._setup_matplotlib_font()

    def _setup_matplotlib_font(self):
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        print("Matplotlib 已設定中文字體。")

    def get_latest_data(self, symbols, days=60):
        end = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
        prices = self.loader.load_from_db(symbols, start, end)
        if prices is None or prices.empty:
            return None
        prices.index = pd.to_datetime(prices.index)
        return prices

    def calculate_zscore(self, prices):
        zscores = pd.DataFrame(index=prices.index)
        for symbol in prices.columns:
            rolling_mean = prices[symbol].rolling(20).mean()
            rolling_std = prices[symbol].rolling(20).std()
            zscores[symbol] = (prices[symbol] - rolling_mean) / rolling_std
        return zscores

    def call_ollama(self, prompt):
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt
            )
            return response['response'].strip()
        except Exception as e:
            return f"**Ollama 錯誤**：{e}\n請執行 `ollama pull gpt-oss:20b`"

    def generate_observation_report(self, symbol, prices, zscore):
        z = zscore[symbol].iloc[-1]
        distance = (prices[symbol].iloc[-1] / prices[symbol].rolling(20).mean().iloc[-1] - 1) * 100

        prompt = f"""
        分析 {symbol}：
        z-score：{z:.2f}
        距離均線：{distance:+.1f}%

        請用繁體中文回答：
        - 狀態：是否接近買入/賣空？
        - 建議：觀察多久？
        - 結論：一句話。
        """
        return self.call_ollama(prompt)

    def run_daily_analysis(self, config):
        symbols = config.get("symbols", ['QQQ', 'NVDA', 'TSLA', 'AAPL', 'MSFT'])
        prices = self.get_latest_data(symbols)
        if prices is None:
            print("無資料，跳過分析")
            return

        from strategies.mean_reversion import MeanReversionStrategy
        strategy = MeanReversionStrategy(config, use_db=True)
        signals = strategy.generate_signals(prices)
        latest_signal = signals.iloc[-1]
        zscore = self.calculate_zscore(prices)

        observations = []
        for symbol in symbols:
            obs = self.generate_observation_report(symbol, prices, zscore)
            observations.append(f"### {symbol} 觀察報告\n{obs}\n")

        log = f"# A1 Agent 全天候分析日誌 - {datetime.today().strftime('%Y-%m-%d')}\n\n"
        log += f"**市場標的**：{', '.join(symbols)}\n"
        log += f"**觸發信號**：{sum(abs(latest_signal) > 0)} 檔\n"
        log += f"**觀察名單**：{len(symbols)} 檔\n\n"
        log += "**今日無交易信號**\n\n" if sum(abs(latest_signal) > 0) == 0 else ""
        log += "## 觀察名單\n" + "\n".join(observations) + "\n"

        with open("reports/daily_signal_log.md", "w", encoding="utf-8") as f:
            f.write(log)

        print(f"A1 Agent 分析完成！使用本地 {self.model}")
