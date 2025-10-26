import argparse
import pandas as pd
import matplotlib.pyplot as plt
from core.strategy_factory import StrategyFactory

def run_strategy(strategy_name, config, use_db):
    config["strategy"] = strategy_name
    config["use_db"] = use_db
    factory = StrategyFactory()
    strategy = factory.create_strategy()
    result = strategy.backtest(config=config)
    result["name"] = strategy_name
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-db", action="store_true", help="從 PostgreSQL 載入資料")
    args = parser.parse_args()

    factory = StrategyFactory()
    config = factory.load_config()

    # 執行兩策略（均可使用 DB）
    mr_result = run_strategy("mean_reversion", config.copy(), args.use_db)
    mom_result = run_strategy("momentum", config.copy(), args.use_db)

    # 繪製比較圖
    plt.figure(figsize=(14,7))
    pd.concat([mr_result["cum_ret"], mom_result["cum_ret"]], axis=1).plot()
    plt.title(f"Strategy Comparison (DB: {args.use_db})")
    plt.legend(["Mean Reversion", "Momentum"])
    plt.savefig("reports/phase5_comparison_db_curve.png")
    plt.close()

    # 產生報告
    report = f"""
    # Phase 5 策略比較報告 (DB 版)
    | 策略 | 總報酬 | MDD | 夏普比率 |
    |------|--------|-----|----------|
    | Mean Reversion | {mr_result['total_return']:.2%} | {mr_result['max_drawdown']:.2%} | N/A |
    | Momentum | {mom_result['total_return']:.2%} | {mom_result['max_drawdown']:.2%} | {mom_result['sharpe']:.2f} |

    **資料來源**：{'PostgreSQL' if args.use_db else 'yfinance'}

    **Phase 5 完成 ✅**
    """
    with open("reports/phase5_comparison.md", "w", encoding="utf-8") as f:
        f.write(report.strip())

    print(f"\n=== Phase 5 DB 比較完成 ===")
    print(f"資料來源: {'PostgreSQL' if args.use_db else 'yfinance'}")
    print(f"比較圖: reports/phase5_comparison_db_curve.png")
    print(f"報告: reports/phase5_comparison.md")