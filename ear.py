import os
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import speech_recognition as sr
import numpy as np
import queue
from langdetect import detect, LangDetectException
import json
from datetime import datetime

HISTORY_FILE = "chat_history.json"
WAKE_WORD = "hey kalp"

def record_audio(duration=5, sample_rate=44100):
    """Record audio from the microphone in a Streamlit-compatible way using InputStream."""
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print("⚠️ Stream status:", status)
        q.put(indata.copy())

    try:
        print("🎤 Recording...")
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=callback):
            audio_frames = []
            for _ in range(int(sample_rate / 1024 * duration)):
                audio_frames.append(q.get())
            audio_data = np.concatenate(audio_frames, axis=0)
        print("✅ Recording complete")

        mean_amplitude = np.abs(audio_data).mean()
        print(f"📊 Average audio amplitude: {mean_amplitude:.2f}")
        if mean_amplitude < 50:
            print("❌ Audio is too quiet")
            return None

        return sample_rate, audio_data

    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        return None

def detect_language(text):
    """Detect language of transcribed text."""
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def save_to_history(text, detected_lang):
    """Save the transcript and language to chat history."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "language": detected_lang
    }

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            pass

    history.append(entry)

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    print(f"💾 Chat saved to {HISTORY_FILE}")

def transcribe_audio(sample_rate, audio_data, lang="en-IN"):
    """Convert audio to text using Google Web Speech API."""
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            wav.write(temp_file.name, sample_rate, audio_data)
            temp_file_path = temp_file.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_file_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language=lang)
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"❌ API Error: {e}")
        return ""
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return ""
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def listen_for_wake_word():
    """Continuously listen for the wake word before activating main logic."""
    print("👂 Listening for wake word...")
    while True:
        result = record_audio(duration=3)
        if not result:
            continue

        sample_rate, audio_data = result
        text = transcribe_audio(sample_rate, audio_data).lower().strip()

        print(f"🗣️ Heard: {text}")
        if text.startswith(WAKE_WORD):
            print("👋 Wake word detected.")
            return True
        else:
            print("🔁 Wake word not detected. Listening again...")

def speech_to_text():
    """Main function to transcribe speech and detect language."""
    result = record_audio()
    if result is None:
        return "", ""

    sample_rate, audio_data = result
    text = transcribe_audio(sample_rate, audio_data)
    if not text:
        return "", ""

    detected_lang = detect_language(text)
    print(f"📝 Final Transcription: {text}")
    print(f"🈶 Detected Language: {detected_lang}")
    save_to_history(text, detected_lang)

    return text, detected_lang

# === For CLI Testing ===
if __name__ == "__main__":
    try:
        if listen_for_wake_word():
            text, lang = speech_to_text()
            if text:
                print(f"✅ You said: {text}")
            else:
                print("❌ No text was transcribed.")
    except KeyboardInterrupt:
        print("🛑 Listening interrupted by user.")