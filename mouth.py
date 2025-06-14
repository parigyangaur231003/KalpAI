import os
import platform
import threading

class TextToSpeech:
    def __init__(self, preferred_voice_name="Samantha"):
        self.voice = preferred_voice_name
        self.is_mac = platform.system() == "Darwin"

    def speak(self, text, language='english'):
        def run_speech():
            try:
                safe_text = (
                    text.replace('.', '. ')
                        .replace(',', ', ')
                        .replace("I'm", "I am")
                        .replace("don't", "do not")
                        .replace('"', '')  # prevent shell injection
                        .strip()
                )
                if self.is_mac:
                    os.system(f'say -v {self.voice} "{safe_text}"')
                else:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 180)
                    engine.setProperty('volume', 1.0)
                    engine.say(safe_text)
                    engine.runAndWait()
            except Exception as e:
                print(f"❌ Error during speech: {e}")

        threading.Thread(target=run_speech, daemon=True).start()

    @staticmethod
    def list_voices():
        if platform.system() == "Darwin":
            os.system("say -v '?'")
        else:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for i, voice in enumerate(voices, 1):
                print(f"{i}. Name: {voice.name}, ID: {voice.id}")

# ======================== Test Area ========================
if __name__ == "__main__":
    tts = TextToSpeech(preferred_voice_name="Samantha")
    print("🔊 Speaking test...")
    tts.speak("Hello! I am Kalp AI, your personal assistant.")

    import time
    time.sleep(3)  # Let thread finish

    print("\n📃 Listing available voices:")
    tts.list_voices()