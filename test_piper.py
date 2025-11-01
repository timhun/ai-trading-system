from piper import PiperVoice
import wave

print("Testing Piper TTS with downloaded model...")

try:
    # Load the voice model
    print("Loading voice model...")
    voice = PiperVoice.load("models/en_US-lessac-medium.onnx")
    print("✓ Voice model loaded successfully!")
    
    # Generate speech
    text = "Hello, welcome to the podcast! This is a test of the Piper text to speech system."
    print(f"\nGenerating audio for: '{text}'")
    
    # Collect audio data from synthesize generator
    audio_bytes = b''
    sample_rate = None
    
    for audio_chunk in voice.synthesize(text):
        # Use the audio_int16_bytes property which returns bytes directly
        audio_bytes += audio_chunk.audio_int16_bytes
        if sample_rate is None:
            sample_rate = audio_chunk.sample_rate
    
    # Save to WAV file
    print("Saving audio to output.wav...")
    with wave.open("output.wav", "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    
    print("✓ Audio generated successfully!")
    print(f"✓ Output saved to: output.wav")
    print(f"\nVoice info:")
    print(f"  - Sample rate: {sample_rate} Hz")
    print(f"  - Audio size: {len(audio_bytes)} bytes")
    print(f"  - Duration: {len(audio_bytes) / (sample_rate * 2):.2f} seconds")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
