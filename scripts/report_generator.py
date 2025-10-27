import json
import os
from datetime import datetime
from core.strategy_factory import StrategyFactory
from scripts.a1_agent import A1Agent
from scripts.a2_macro import MacroAnalyst
from scripts.a3_risk import RiskController
from scripts.a6_tuner import ModelTuner

class ReportGenerator:
    def __init__(self, config_path="config/agents.json", notif_path="config/notifications.json"):
        # 載入 agents config
        if os.path.exists(config_path):
            with open(config_path) as f:
                self.agents_config = json.load(f)
        else:
            print(f"警告：找不到 {config_path}，跳過 A2/A3/A6")
            self.agents_config = {}

        # 載入通知 config
        if os.path.exists(notif_path):
            with open(notif_path) as f:
                self.notif_config = json.load(f)
        else:
            print(f"警告：找不到 {notif_path}，跳過發送")
            self.notif_config = {}

        self.factory = StrategyFactory()
        self.config = self.factory.load_config()
        self.agent = A1Agent()

    def generate_report(self):
        print("啟動 A1 Agent 分析...")
        self.agent.run_daily_analysis(self.config)

        # 讀取 A1 結果
        a1_path = "reports/daily_signal_log.md"
        a1_log = open(a1_path, encoding="utf-8").read() if os.path.exists(a1_path) else "**A1 無輸出**"

        # A2 宏觀
        a2_log = "**A2 跳過**"
        if "fred" in self.agents_config:
            try:
                a2 = MacroAnalyst(self.agents_config["fred"])
                a2_log = a2.run()
            except Exception as e:
                a2_log = f"**A2 錯誤**：{e}"

        # A3 風險
        a3_log = "**A3 跳過**"
        if True:
            try:
                a3 = RiskController(self.config)
                import numpy as np
                strategy_ret = np.random.randn(100) * 0.01  # 模擬
                a3_log, _ = a3.run(strategy_ret)
            except Exception as e:
                a3_log = f"**A3 錯誤**：{e}"

        # A6 決策
        final = "**A6 跳過**"
        signal = "NVDA 買入" if "買入" in a1_log else "無"
        if "gemini" in self.agents_config:
            try:
                a6 = ModelTuner(self.agents_config["gemini"])
                final = a6.final_decision(a1_log, a2_log, a3_log, signal)
            except Exception as e:
                final = f"**A6 錯誤**：{e}"

        # 最終報告
        report = f"# 最終投資報告 - {datetime.today().strftime('%Y-%m-%d')}\n\n"
        report += f"{a1_log}\n\n{a2_log}\n\n{a3_log}\n\n## 首席投資官建議\n{final}\n"

        final_path = "reports/final_report.md"
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"最終報告生成：{final_path}")
        return report

    def send_report(self, report):
        if not self.notif_config:
            print("無通知設定，跳過發送")
            return

        # Telegram
        if "telegram" in self.notif_config:
            try:
                from telegram import Bot
                from telegram.constants import ParseMode
                import asyncio

                bot = Bot(token=self.notif_config["telegram"]["bot_token"])
                chat_id = self.notif_config["telegram"]["chat_id"]

                # 自動驗證 chat_id 是否有效
                async def validate_and_send():
                    try:
                        await bot.send_message(
                            chat_id=chat_id,
                            text="AI 量化系統測試訊息",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        # 測試成功，再發正式報告
                        await bot.send_message(
                            chat_id=chat_id,
                            text=report[:4000],
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return True
                    except Exception as e:
                        if "bots can't send messages to bots" in str(e):
                            raise Exception("錯誤：chat_id 是 Bot ID！請改用您的個人 ID。")
                        elif "chat not found" in str(e):
                            raise Exception(f"錯誤：找不到 chat_id {chat_id}，請確認是否已與 Bot 對話。")
                        else:
                            raise e

                asyncio.run(validate_and_send())
                print("Telegram 發送成功")
            except Exception as e:
                print(f"Telegram 失敗: {e}")
                print("解決方式：")
                print("  1. 找 @userinfobot 取得您的 ID")
                print("  2. 更新 config/notifications.json 的 chat_id")
                print("  3. 先與 Bot 對話（發 'hi'）")

        # Slack
        if "slack" in self.notif_config:
            try:
                from slack_sdk import WebClient
                client = WebClient(token=self.notif_config["slack"]["token"])
                client.chat_postMessage(
                    channel=self.notif_config["slack"]["channel"],
                    text=report[:4000]
                )
                print("Slack 發送成功")
            except Exception as e:
                print(f"Slack 失敗: {e}")

        # Email
        if "email" in self.notif_config:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                msg = MIMEMultipart()
                msg['From'] = self.notif_config["email"]["sender"]
                msg['To'] = self.notif_config["email"]["receiver"]
                msg['Subject'] = f"AI 量化報告 - {datetime.today().strftime('%Y-%m-%d')}"

                msg.attach(MIMEText(report, 'plain', 'utf-8'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(self.notif_config["email"]["sender"], self.notif_config["email"]["app_password"])
                server.sendmail(self.notif_config["email"]["sender"], self.notif_config["email"]["receiver"], msg.as_string())
                server.quit()
                print("Email 發送成功")
            except Exception as e:
                print(f"Email 失敗: {e}")

if __name__ == "__main__":
    generator = ReportGenerator()
    report = generator.generate_report()
    generator.send_report(report)
    print("每日報告流程完成！")
