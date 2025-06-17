import os
import platform
import subprocess
import uuid
import re

class TextToSpeech:
    def __init__(self, preferred_voice_name="Samantha"):
        self.voice = preferred_voice_name
        self.is_mac = platform.system() == "Darwin"

    def speak(self, text, language='english'):
        """
        Speak the given text aloud using macOS `say` + `afplay` or pyttsx3 on other platforms.
        """
        try:
            safe_text = self._expand_and_sanitize(text)

            if not safe_text:
                print("⚠️ Empty text received for TTS.")
                return

            if self.is_mac:
                filename = f"/tmp/{uuid.uuid4().hex}.aiff"
                try:
                    subprocess.run(["say", "-v", self.voice, "-o", filename, safe_text], check=True)
                    subprocess.run(["afplay", filename], check=True)
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)
            else:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 175)
                engine.setProperty('volume', 1.0)

                # Try to match voice
                voices = engine.getProperty('voices')
                matched = False
                for voice in voices:
                    if self.voice.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        matched = True
                        break

                if not matched:
                    print(f"⚠️ Preferred voice '{self.voice}' not found. Using default.")

                engine.say(safe_text)
                engine.runAndWait()

        except Exception as e:
            print(f"❌ Error during speech synthesis: {e}")

    def _expand_and_sanitize(self, text):
        """
        Expand common contractions and sanitize text for better TTS clarity.
        """
        contractions = {
            r"\bI'm\b": "I am", r"\bI've\b": "I have", r"\bI'll\b": "I will", r"\bI'd\b": "I would",
            r"\byou're\b": "you are", r"\byou've\b": "you have", r"\byou'll\b": "you will",
            r"\bhe's\b": "he is", r"\bshe's\b": "she is", r"\bit's\b": "it is",
            r"\bcan't\b": "cannot", r"\bdon't\b": "do not", r"\bwon't\b": "will not",
            r"\bdoesn't\b": "does not", r"\bdidn't\b": "did not",
            r"\bthat's\b": "that is", r"\bthere's\b": "there is", r"\bwhat's\b": "what is",
            r"\bLet's\b": "Let us"
        }

        for pattern, replacement in contractions.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Remove problematic characters
        return text.replace('"', '').replace("'", "").replace("&", "and").strip()

    @staticmethod
    def list_voices():
        """
        Print a list of available TTS voices.
        """
        if platform.system() == "Darwin":
            print("🗣️ Available macOS voices:")
            os.system("say -v '?'")
        else:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for i, voice in enumerate(voices, 1):
                print(f"{i}. Name: {voice.name}, ID: {voice.id}")

# === Test Case ===
if __name__ == "__main__":
    tts = TextToSpeech(preferred_voice_name="Samantha")  # Use "Alex" or others as needed
    print("🔊 Speaking test message...")
    tts.speak("Do not be shy or hesitant. I am here to listen to you.")
    print("\n📃 Listing available voices:")
    tts.list_voices()
