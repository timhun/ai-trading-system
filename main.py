import pandas as pd
from core.strategy_factory import StrategyFactory

if __name__ == "__main__":
    factory = StrategyFactory()
    config = factory.load_config()  # 取得 config
    strategy = factory.create_strategy()
    result = strategy.backtest(config=config)  # 傳入 config

    print(f"\n=== Phase 3 模組化回測 ===")
    print(f"策略: {type(strategy).__name__}")
    print(f"總報酬: {result['total_return']:.2%}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"權益曲線: reports/phase3_equity_curve.png")
    print(f"Phase 3 完成 ✅")
