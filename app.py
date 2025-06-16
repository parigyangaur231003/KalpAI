import os
import json
import time
import platform
import streamlit as st
from datetime import datetime
from threading import Thread
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import wave

# ✅ Must be first Streamlit command
st.set_page_config(layout="centered", page_title="Kalp AI")

from groq_agent import get_groq_llm
from mouth import TextToSpeech  # assumes speak() is blocking
from eye import analyze_emotion
from prompts.system_prompt.system_prompt import system_prompt

# === Init ===
llm = get_groq_llm()
tts = TextToSpeech()
chat_history = []
session_start = datetime.now()

EXIT_PHRASES = {
    "thank you", "thanks", "you solved my problem",
    "problem solved", "appreciate it", "that helped"
}
OFF_TOPIC_PHRASES = {
    "who is", "tell me about", "what is", "prime minister", "actor", "movie",
    "president", "cricketer", "capital of", "current news", "weather", "joke"
}

# === Utility Functions ===
def should_end_session(text):
    return any(phrase in text.lower() for phrase in EXIT_PHRASES)

def is_off_topic(text):
    return any(phrase in text.lower() for phrase in OFF_TOPIC_PHRASES)

def save_chat_history():
    os.makedirs("DATA", exist_ok=True)
    filename = os.path.join("DATA", f"kalpai_session_{session_start.strftime('%Y%m%d_%H%M%S')}.json")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=4, ensure_ascii=False)
        st.success(f"💾 Chat history saved: {filename}")
    except Exception as e:
        st.error(f"❌ Failed to save chat: {e}")

def record_audio(duration=6, samplerate=44100, filename="temp_audio.wav"):
    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        write(filename, samplerate, recording)
        return filename
    except Exception as e:
        st.error(f"❌ Recording failed: {e}")
        return None

def is_valid_wav(filename):
    try:
        with wave.open(filename, 'rb') as f:
            return f.getnchannels() > 0
    except:
        return False

def transcribe_uploaded_audio(file_path):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="en-IN")
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        return f"❌ Error: {e}"

def estimate_tts_duration(text):
    words = len(text.split())
    estimated_seconds = words / 2.5  # ~150 WPM = 2.5 WPS
    return min(15, max(2, estimated_seconds))

def process_input(audio_file):
    if not audio_file or not os.path.exists(audio_file):
        return "❌ Error: Audio file was not recorded properly."

    if not is_valid_wav(audio_file):
        return "❌ Error: Recorded file is not a valid WAV format."

    user_input = transcribe_uploaded_audio(audio_file)
    os.remove(audio_file)

    if not user_input or user_input.strip().startswith("❌"):
        return user_input or "❌ Sorry, I couldn't understand. Try speaking louder or clearly."

    if is_off_topic(user_input):
        warning = (
            "I'm here to support your mental and emotional well-being. "
            "Let’s stay focused on what you’re feeling. I can’t answer non-mental health questions."
        )
        tts.speak(warning, "english")
        return warning

    emotion = "neutral"
    Thread(target=lambda: analyze_emotion(text=user_input, use_facial=False), daemon=True).start()

    context = system_prompt("neutral")
    query = f"{context}\nUser: {user_input}"

    try:
        response = llm.invoke(query)
        response_text = getattr(response, 'content', str(response))
    except Exception as e:
        response_text = f"❌ LLM error: {e}"

    tts.speak(response_text, "english")

    chat_history.append({
        "user": user_input,
        "assistant": response_text,
        "emotion": emotion,
        "language": "english",
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    if should_end_session(user_input):
        goodbye = (
            "I'm really glad I could help. Remember, I’m always here when you need someone to talk to. "
            "Take care of yourself!"
        )
        tts.speak(goodbye, "english")
        save_chat_history()
        return goodbye

    return response_text


# === Streamlit UI ===
st.markdown("""
    <style>
        html, body, [data-testid="stApp"] {
            background-color: #000000 !important;
            color: white !important;
            height: 100vh;
            overflow-x: hidden;
        }
        .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding-top: 0 !important;
        }
        .stButton > button {
            background-color: #000000;
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 12px 24px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .output-text {
            font-size: 20px;
            color: white;
            margin-top: 40px;
            text-align: center;
        }
        #MainMenu, header, footer, .stDeployButton {
            visibility: hidden;
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

st.image("kalp.gif", use_container_width=True)
st.markdown("""
    <div style='text-align: center; margin-top: -10px;'>
        <span style='font-size: 13px;'>🤗 Hello! Welcome to KalpAI, I'm your compassionate companion for emotional support and well-being.</span>
    </div>
""", unsafe_allow_html=True)

# === Conversation Loop ===
if "conversation_active" not in st.session_state:
    st.session_state["conversation_active"] = False

# === Show Start Button if not active ===
if not st.session_state["conversation_active"]:
    if st.button("🗣️ Let's start talking"):
        st.session_state["conversation_active"] = True
        st.rerun()

# === Active Listening Loop ===
if st.session_state["conversation_active"]:
    st.markdown("🟢 **KalpAI is active...** _(Say 'thank you' to end)_")

    # 👂🏼 Only show spinner during audio capture
    with st.spinner("👂🏼 Listening to your voice..."):
        audio_file = record_audio()

    # 🎤 Process input and respond (includes TTS)
    response = process_input(audio_file)

    # ✅ Handle session termination
    if any(phrase in response.lower() for phrase in EXIT_PHRASES):
        st.session_state["conversation_active"] = False
        st.success("🛑 Conversation ended based on your response.")
        st.stop()  # 👈 This stops execution; UI will reload cleanly
    elif "❌ Sorry, I couldn't understand" in response:
        time.sleep(2)
        st.rerun()
    else:
        st.rerun()
