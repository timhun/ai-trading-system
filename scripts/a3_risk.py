import pandas as pd
import numpy as np

class RiskController:
    def __init__(self, config):
        self.config = config

    def calculate_var(self, returns, confidence=0.95):
        return np.percentile(returns, (1-confidence)*100)

    def kelly_fraction(self, win_rate, avg_win, avg_loss):
        return win_rate / avg_loss - (1 - win_rate) / avg_win if avg_win > 0 else 0

    def run(self, strategy_ret):
        var = self.calculate_var(strategy_ret)
        kelly = self.kelly_fraction(0.55, 0.02, 0.015)  # 假設參數
        risk = {
            "VaR_95": f"{var:.2%}",
            "Kelly_部位": f"{kelly:.1%}",
            "建議止損": "-5%"
        }
        log = f"## 風險控管\n- VaR (95%): {risk['VaR_95']}\n- Kelly 部位: {risk['Kelly_部位']}\n- 止損: {risk['建議止損']}\n"
        return log, risk
