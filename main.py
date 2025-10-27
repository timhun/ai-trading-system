import argparse
import os
import sys

def safe_import():
    try:
        from scripts.report_generator import ReportGenerator
        return ReportGenerator
    except ImportError as e:
        print(f"錯誤：無法匯入 ReportGenerator。請檢查 scripts/report_generator.py 檔案路徑。")
        print(f"詳細錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="生成並發送每日報告")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()

    if args.report:
        print("啟動每日報告生成與發送...")
        ReportGenerator = safe_import()
        generator = ReportGenerator()
        report = generator.generate_report()
        generator.send_report(report)
    elif args.live:
        print("即將啟動模擬交易...")
        # trader 邏輯
    elif args.explain:
        print("啟動 A1 Agent 解釋...")
        from scripts.a1_agent import A1Agent
        agent = A1Agent()
        agent.run_daily_analysis({})
    else:
        print("請使用 --report / --live / --explain")
