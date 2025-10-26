import alpaca_trade_api as tradeapi
import pandas as pd
import json
from datetime import datetime
import time
import logging

class AlpacaTrader:
    def __init__(self, config_path="config/alpaca.json"):
        with open(config_path) as f:
            creds = json.load(f)
        self.api = tradeapi.REST(
            creds["api_key"],
            creds["secret_key"],
            creds["base_url"],
            api_version='v2'
        )
        self.account = self.api.get_account()
        print(f"模擬盤帳戶：{self.account.cash} USD")

    def get_positions(self):
        return {p.symbol: float(p.qty) for p in self.api.list_positions()}

    def place_order(self, symbol, qty, side):
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=abs(qty),
                side=side,
                type='market',
                time_in_force='gtc'
            )
            print(f"下單成功：{side.upper()} {qty} {symbol}")
            return True
        except Exception as e:
            print(f"下單失敗 {symbol}: {e}")
            return False

    def close_position(self, symbol):
        try:
            self.api.close_position(symbol)
            print(f"平倉 {symbol}")
        except:
            pass

    def run_live_trading(self, config, agent):
        symbols = config["symbols"]
        cash = float(self.account.cash)
        positions = self.get_positions()
        target_value = cash * 0.2  # 每檔最多 20%

        print(f"\n=== 開始實時交易模式 ===")
        print(f"可用資金：{cash:.2f} USD")

        # 獲取最新信號
        prices = agent.get_latest_data(symbols)
        if prices is None:
            return

        from strategies.mean_reversion import MeanReversionStrategy
        strategy = MeanReversionStrategy(config, use_db=True)
        signals = strategy.generate_signals(prices)
        latest_signal = signals.iloc[-1]

        orders = []
        for symbol in symbols:
            sig = latest_signal[symbol]
            current_qty = positions.get(symbol, 0)

            if sig > 0 and current_qty <= 0:  # 買入
                qty = max(1, int(target_value / prices[symbol].iloc[-1]))
                if self.place_order(symbol, qty, 'buy'):
                    orders.append(f"BUY {qty} {symbol}")

            elif sig < 0 and current_qty >= 0:  # 賣空（模擬盤不支援，改為賣出）
                qty = -current_qty if current_qty > 0 else 1
                if self.place_order(symbol, qty, 'sell'):
                    orders.append(f"SELL {qty} {symbol}")

            elif sig == 0 and current_qty != 0:  # 無信號，平倉
                self.close_position(symbol)
                orders.append(f"CLOSE {symbol}")

        # 記錄交易日誌
        log = f"# 實時交易日誌 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        log += f"**帳戶現金**：{cash:.2f} USD\n"
        log += f"**執行指令**：{len(orders)}\n\n"
        log += "\n".join([f"- {o}" for o in orders]) if orders else "- 無交易\n"
        log += f"\n**部位狀態**：\n"
        for sym, qty in positions.items():
            if qty != 0:
                log += f"- {sym}: {qty} 股\n"

        with open("reports/trade_log.md", "a", encoding="utf-8") as f:
            f.write(log + "\n---\n")

        print(f"交易日誌已更新：reports/trade_log.md")

if __name__ == "__main__":
    from core.strategy_factory import StrategyFactory
    from scripts.a1_agent import A1Agent
    factory = StrategyFactory()
    config = factory.load_config()
    trader = AlpacaTrader()
    agent = A1Agent()
    trader.run_live_trading(config, agent)
