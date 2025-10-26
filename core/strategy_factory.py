import importlib
import json

class StrategyFactory:
    @staticmethod
    def load_config():
        with open("config/config.json", "r", encoding="utf-8-sig") as f:
            return json.load(f)

    @staticmethod
    def create_strategy():
        config = StrategyFactory.load_config()
        strategy_name = config["strategy"]
        module = importlib.import_module(f"strategies.{strategy_name}")
        # 正確轉換：mean_reversion → MeanReversionStrategy
        class_name = "".join(part.capitalize() for part in strategy_name.split("_")) + "Strategy"
        strategy_class = getattr(module, class_name)
        return strategy_class(config)