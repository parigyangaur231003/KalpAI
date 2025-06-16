import os
import platform
import subprocess
import uuid

class TextToSpeech:
    def __init__(self, preferred_voice_name="Samantha"):
        self.voice = preferred_voice_name
        self.is_mac = platform.system() == "Darwin"

    def speak(self, text, language='english'):
        """
        Speak the given text aloud using platform-specific voice engine.
        macOS uses `say` with `afplay` to prevent truncation.
        Windows/Linux uses pyttsx3.
        """
        try:
            safe_text = (
                text.replace('"', '')
                    .replace("'", "")
                    .replace("&", "and")
                    .replace("I'm", "I am")
                    .replace("don't", "do not")
                    .strip()
            )

            if self.is_mac:
                filename = f"/tmp/{uuid.uuid4().hex}.aiff"
                # Generate AIFF file
                subprocess.run(["say", "-v", self.voice, "-o", filename, safe_text], check=True)
                # Play AIFF file (blocking)
                subprocess.run(["afplay", filename], check=True)
                os.remove(filename)  # Clean up

            else:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 180)
                engine.setProperty('volume', 1.0)

                # Try setting preferred voice
                voices = engine.getProperty('voices')
                matched = False
                for voice in voices:
                    if self.voice.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        matched = True
                        break

                if not matched:
                    print(f"⚠️ Preferred voice '{self.voice}' not found. Using default voice.")

                engine.say(safe_text)
                engine.runAndWait()

        except Exception as e:
            print(f"❌ Error during speech synthesis: {e}")

    @staticmethod
    def list_voices():
        """
        List available voices for the platform.
        """
        if platform.system() == "Darwin":
            os.system("say -v '?'")
        else:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for i, voice in enumerate(voices, 1):
                print(f"{i}. Name: {voice.name}, ID: {voice.id}")

# ======================== Test Area ========================
if __name__ == "__main__":
    tts = TextToSpeech(preferred_voice_name="Samantha")  # Use "Alex", "Victoria", etc. on macOS
    print("🔊 Speaking test...")
    tts.speak("Hello! I am Kalp AI, your compassionate companion.")
    print("\n📃 Listing available voices:")
    tts.list_voices()
