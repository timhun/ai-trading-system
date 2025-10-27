class ModelTuner:
    def __init__(self):
        with open("config/openai.json") as f:
            config = json.load(f)
        openai.api_key = config["api_key"]
        self.model = config["model"]

    def final_decision(self, a1_log, a2_log, a3_log, signal):
        prompt = f"""
        你是首席投資官。以下是今日分析：

        {a1_log}
        {a2_log}
        {a3_log}

        請給出最終投資建議（繁體中文）：
        1. 是否執行交易？
        2. 部位大小？
        3. 風險評估？
        4. 一句總結。
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"**GPT 錯誤**：{e}"