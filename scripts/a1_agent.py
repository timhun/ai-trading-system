import ollama
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from scripts.db_loader import DBLoader

class A1Agent:
    """
    A1Agent 全天候分析版：
    1. 從 PostgreSQL 載入數據。
    2. 生成交易信號 + 觀察名單。
    3. LLM 生成「交易解釋」與「觀察報告」。
    4. 輸出日誌 + 價格圖 + z-score 圖。
    """
    def __init__(self):
        self.model = "gpt-oss:20b"
        self.loader = DBLoader()
        self._setup_matplotlib_font()

    def _setup_matplotlib_font(self):
        """設定 Matplotlib 使用支援中文的字體。"""
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'PingFang TC', 'SimHei', 'Arial Unicode MS']
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
        """計算每檔股票的 z-score（均值回歸）"""
        zscores = pd.DataFrame(index=prices.index)
        for symbol in prices.columns:
            rolling_mean = prices[symbol].rolling(20).mean()
            rolling_std = prices[symbol].rolling(20).std()
            zscores[symbol] = (prices[symbol] - rolling_mean) / rolling_std
        return zscores

    def generate_signal_explanation(self, symbol, signal, prices, config):
        recent_ret = prices[symbol].pct_change().tail(5).mean()
        window = 20
        rolling_mean = prices[symbol].rolling(window=window).mean()
        rolling_std = prices[symbol].rolling(window=window).std()
        latest_price = prices[symbol].iloc[-1]
        latest_z = (latest_price - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]

        prompt = f"""
        你是一位專業量化交易分析師。以下是今日交易信號和相關數據：

        標的：{symbol}
        信號：{'買入' if signal > 0 else '賣空' if signal < 0 else '無'}
        策略：均值回歸 (基於 {window} 日移動平均)
        最新價格：{latest_price:.2f}
        最新 z-score：{latest_z:.2f}
        近 5 日平均報酬：{recent_ret:.2%}
        市場環境：科技股 ({', '.join(prices.columns)})

        請用 **繁體中文** 解釋：
        1. 為何今日觸發此信號 (價格相對於均值是否偏離過大)？
        2. 交易情緒評估（市場是否過熱/超賣）。
        3. 建議持倉時間與技術止損點。
        4. 一句總結。

        格式：
        **信號解釋**：...
        **交易情緒**：...
        **建議**：...
        **結論**：...
        """
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            return response['response']
        except Exception as e:
            return f"Ollama 呼叫失敗: {e}"

    def generate_observation_report(self, symbol, prices, zscore):
        latest_z = zscore[symbol].iloc[-1]
        recent_ret = prices[symbol].pct_change().tail(5).mean()
        distance = (prices[symbol].iloc[-1] / prices[symbol].rolling(20).mean().iloc[-1] - 1) * 100

        prompt = f"""
        你是一位專業量化交易分析師。以下是 {symbol} 的最新觀察數據：

        最新 z-score：{latest_z:.2f}
        距離均值：{distance:+.1f}%
        近 5 日報酬：{recent_ret:+.2%}
        市場環境：科技股

        請用 **繁體中文** 分析：
        1. 目前是否接近觸發買入/賣空？
        2. 建議觀察時間與預期觸發點
        3. 一句結論

        格式：
        **{symbol} 觀察報告**：
        - 狀態：...
        - 建議：...
        - 結論：...
        """
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            return response['response']
        except Exception as e:
            return f"Ollama 呼叫失敗: {e}"

    def plot_signal_chart(self, prices, signals, symbol):
        fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        prices[symbol].plot(ax=ax[0], title=f"{symbol} 價格走勢")
        ax[0].axhline(prices[symbol].mean(), color='r', linestyle='--', label='歷史均值')
        ax[0].legend()
        signals[symbol].plot(ax=ax[1], kind='bar', title="交易信號", color='green')
        ax[1].axhline(0, color='k', linewidth=0.5)
        plt.tight_layout()
        plt.savefig("reports/daily_signal_chart.png")
        plt.close()

    def plot_zscore_chart(self, prices, zscore, signals):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        prices.mean(axis=1).plot(ax=ax1, title="市場平均價格")
        ax1.axhline(prices.mean(axis=1).mean(), color='r', linestyle='--')
        zscore.plot(ax=ax2, title="z-score (觸發門檻 2.0)", alpha=0.7)
        ax2.axhline(2.0, color='r', linestyle='--', alpha=0.7, label='賣空門檻')
        ax2.axhline(-2.0, color='g', linestyle='--', alpha=0.7, label='買入門檻')
        ax2.axhline(0, color='k', linewidth=0.5)
        ax2.legend()
        signals.sum(axis=1).plot(ax=ax3, kind='bar', title="總信號數", color='orange')
        plt.tight_layout()
        plt.savefig("reports/daily_zscore_analysis.png", dpi=150)
        plt.close()

    def run_daily_analysis(self, config):
        symbols = config["symbols"]
        prices = self.get_latest_data(symbols)
        if prices is None:
            print("無資料，跳過分析")
            return

        try:
            from strategies.mean_reversion import MeanReversionStrategy
            strategy = MeanReversionStrategy(config, use_db=True)
            signals = strategy.generate_signals(prices)
            latest_signal = signals.iloc[-1]
        except ImportError:
            print("錯誤: 無法匯入 MeanReversionStrategy。")
            return

        zscore = self.calculate_zscore(prices)

        # 生成解釋
        explanations = []
        for symbol in symbols:
            sig = latest_signal[symbol]
            if sig != 0:
                exp = self.generate_signal_explanation(symbol, sig, prices, config)
                explanations.append(f"### {symbol} ({'買入' if sig > 0 else '賣空'})\n{exp}\n")

        # 生成觀察報告（全天候）
        observations = []
        for symbol in symbols:
            obs = self.generate_observation_report(symbol, prices, zscore)
            observations.append(f"### {obs}\n")

        # 繪圖
        if "NVDA" in symbols:
            self.plot_signal_chart(prices, signals, "NVDA")
        elif symbols:
            self.plot_signal_chart(prices, signals, symbols[0])
        self.plot_zscore_chart(prices, zscore, signals)

        # 產生日誌
        log = f"# A1 Agent 全天候分析日誌 - {datetime.today().strftime('%Y-%m-%d')}\n\n"
        log += f"**市場標的**：{', '.join(symbols)}\n"
        log += f"**觸發信號**：{sum(abs(latest_signal) > 0)} 檔\n"
        log += f"**觀察名單**：{len(symbols)} 檔\n\n"

        if explanations:
            log += "## 交易信號\n" + "\n".join(explanations) + "\n"
        else:
            log += "**今日無交易信號**\n\n"

        log += "## 觀察名單\n" + "\n".join(observations) + "\n"
        log += f"![價格與信號](daily_signal_chart.png)\n"
        log += f"![z-score 分析](daily_zscore_analysis.png)\n"

        with open("reports/daily_signal_log.md", "w", encoding="utf-8") as f:
            f.write(log)

        print(f"A1 Agent 全天候分析完成！")
        print(f"日誌：reports/daily_signal_log.md")
        print(f"圖表1：reports/daily_signal_chart.png")
        print(f"圖表2：reports/daily_zscore_analysis.png")

if __name__ == "__main__":
    try:
        from core.strategy_factory import StrategyFactory
        factory = StrategyFactory()
        config = factory.load_config()
    except ImportError:
        print("錯誤：無法匯入 StrategyFactory。")
        exit()
    agent = A1Agent()
    agent.run_daily_analysis(config)
