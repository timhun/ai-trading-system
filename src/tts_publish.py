import os, datetime, subprocess, wave
from src.progress import append_block

# -----------------------------
# 🧩 主要設定
# -----------------------------
PIPER_MODEL = "assets/piper/zh_CN-huayan-medium.onnx"
PIPER_CONFIG = "assets/piper/zh_CN-huayan-medium.onnx.json"
INTRO_MP3 = "assets/audio/intro.mp3"

# -----------------------------
# 🗣️ Piper TTS
# -----------------------------
def synthesize_with_piper(text: str, output_path: str):
    from piper import PiperVoice

    if not os.path.exists(PIPER_MODEL):
        raise FileNotFoundError("❌ 找不到 Piper 模型")

    print("🗣️ 使用 Piper 語音引擎...")
    voice = PiperVoice.load(PIPER_MODEL, PIPER_CONFIG)
    audio_bytes, sample_rate = b"", None

    for chunk in voice.synthesize(text):
        audio_bytes += chunk.audio_int16_bytes
        sample_rate = sample_rate or chunk.sample_rate

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    print(f"✅ Piper 成功產生：{output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")

# -----------------------------
# 🌐 Edge TTS 備援
# -----------------------------
def synthesize_with_edge_tts(text: str, output_path: str, voice="zh-CN-XiaoruiNeural"):
    try:
        import edge_tts
    except ImportError:
        os.system("pip install edge-tts -q")
        import edge_tts

    print("🌐 使用 Edge-TTS 備援語音...")
    import asyncio

    async def _run():
        tts = edge_tts.Communicate(text, voice)
        await tts.save(output_path)

    asyncio.run(_run())
    print(f"✅ Edge-TTS 成功產生：{output_path}")

# -----------------------------
# 🎧 混音與轉檔
# -----------------------------
def convert_to_mp3(input_wav: str, output_mp3: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_wav,
        "-codec:a", "libmp3lame",
        "-qscale:a", "2",
        output_mp3,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"🎵 已轉換為 MP3：{output_mp3}")

def mix_intro(intro_path, audio_path, output_path):
    if not os.path.exists(intro_path):
        print("⚠️ 無 intro.mp3，略過混音")
        return False
    cmd = [
        "ffmpeg", "-y",
        "-i", intro_path, "-i", audio_path,
        "-filter_complex", "[0:0][1:0]concat=n=2:v=0:a=1[a]",
        "-map", "[a]", output_path,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"🎶 已混音輸出：{output_path}")
    return True

# -----------------------------
# 🚀 主流程
# -----------------------------
def main():
    today = datetime.date.today().isoformat()
    logs = []

    texts = {
        "short_term": "這是一段短線策略的Podcast講稿範例，使用Piper語音合成測試。",
        "long_term": "這是一段長線投資策略的Podcast講稿範例，使用Piper語音合成測試。"
    }

    for key, text in texts.items():
        wav_path = f"outputs/audio/episode_{today}_{key}.wav"
        mp3_path = wav_path.replace(".wav", ".mp3")
        final_mp3 = f"outputs/audio/episode_{today}_{key}_final.mp3"

        try:
            # --- 優先使用 Piper ---
            try:
                synthesize_with_piper(text, wav_path)
            except Exception as e:
                print(f"⚠️ Piper 失敗：{e}")
                synthesize_with_edge_tts(text, wav_path)

            # --- 轉 MP3 + 混音 ---
            convert_to_mp3(wav_path, mp3_path)
            mix_intro(INTRO_MP3, mp3_path, final_mp3)

            msg = f"✅ {key} 音訊已完成 → {final_mp3}"
            logs.append(msg)
            print(msg)

        except Exception as e:
            msg = f"❌ {key} 生成失敗: {e}"
            logs.append(msg)
            print(msg)

    append_block("TTS & Publish Bot", logs)
    print("📝 已更新 logs/progress.md")

if __name__ == "__main__":
    main()
