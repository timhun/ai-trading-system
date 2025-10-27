import fredapi as fa
import pandas as pd
from datetime import datetime

class MacroAnalyst:
    def __init__(self, api_key):
        self.fred = fa.Fred(api_key=api_key)

    def get_macro_data(self):
        indicators = {
            'FEDFUNDS': '聯邦基金利率',
            'UNRATE': '失業率',
            'CPIAUCSL': 'CPI',
            'GDP': 'GDP'
        }
        data = {}
        for code, name in indicators.items():
            series = self.fred.get_series(code)
            latest = series.iloc[-1] if not series.empty else None
            prev = series.iloc[-2] if len(series) > 1 else None
            change = (latest - prev) / prev * 100 if prev and prev != 0 else 0
            data[name] = {"最新": latest, "變化": f"{change:+.2f}%"}
        return data

    def run(self):
        data = self.get_macro_data()
        log = f"## 宏觀經濟分析 - {datetime.today().strftime('%Y-%m-%d')}\n\n"
        for name, vals in data.items():
            log += f"- **{name}**：{vals['最新']} ({vals['變化']})\n"
        with open("reports/macro_YYYYMMDD.json", "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, ensure_ascii=False, indent=2)
        return log
