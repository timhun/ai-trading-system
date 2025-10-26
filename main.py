import argparse
from core.strategy_factory import StrategyFactory

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-db", action="store_true")
    parser.add_argument("--explain", action="store_true", help="啟用 A1 Agent 解釋今日信號")
    args = parser.parse_args()

    if args.explain:
        from scripts.a1_agent import A1Agent
        factory = StrategyFactory()
        config = factory.load_config()
        agent = A1Agent()
        agent.run_daily_analysis(config)
    else:
        # 原有比較邏輯...
        pass  # 保留 Phase 5 邏輯
