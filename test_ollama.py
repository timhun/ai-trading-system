from ollama import Client

client = Client(host="http://localhost:11434")

print("=== 測試 Ollama ===")

# 測試 1: 簡單問題
print("\n1️⃣ 測試簡單生成...")
try:
    resp = client.generate(
        model="gpt-oss:20B",
        prompt="請回答：1+1等於多少？",
        stream=False
    )
    print(f"回應類型: {type(resp)}")
    print(f"回應內容: {resp}")
    
    if isinstance(resp, dict):
        print(f"response 欄位: {resp.get('response', '(無)')}")
except Exception as e:
    print(f"❌ 錯誤: {e}")

# 測試 2: 串流模式
print("\n2️⃣ 測試串流模式...")
try:
    resp = client.generate(
        model="gpt-oss:20B",
        prompt="請說：你好",
        stream=True
    )
    
    text = ""
    for chunk in resp:
        if hasattr(chunk, 'response'):
            text += chunk.response
        elif isinstance(chunk, dict):
            text += chunk.get('response', '')
    
    print(f"串流回應長度: {len(text)}")
    print(f"串流內容: {text}")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")

# 測試 3: JSON 生成
print("\n3️⃣ 測試 JSON 生成...")
try:
    resp = client.generate(
        model="gpt-oss:20B",
        prompt='請只輸出 JSON: {"test": true}',
        stream=False
    )
    
    if isinstance(resp, dict):
        content = resp.get('response', '')
        print(f"JSON 測試長度: {len(content)}")
        print(f"JSON 測試內容: {content}")
    else:
        print(f"非預期格式: {resp}")
        
except Exception as e:
    print(f"❌ 錯誤: {e}")

print("\n=== 測試完成 ===")
