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

# === Streamlit Page Config ===
st.set_page_config(layout="centered", page_title="Kalp AI")

# === Internal Modules ===
from groq_agent import get_groq_llm
from mouth import TextToSpeech
from eye import analyze_emotion
from prompts.system_prompt.system_prompt import system_prompt

# === Init ===
llm = get_groq_llm()
tts = TextToSpeech()
chat_history = []
session_start = datetime.now()

EXIT_PHRASES = {"thank you", "thanks", "you solved my problem", "problem solved", "appreciate it", "that helped"}
OFF_TOPIC_PHRASES = {"who is", "tell me about", "what is", "prime minister", "actor", "movie", "president", "cricketer", "capital of", "current news", "weather", "joke"}

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

def record_audio(duration=6, samplerate=16000, filename="temp_audio.wav"):
    try:
        sd.default.samplerate = samplerate
        sd.default.channels = 1
        rec = sd.rec(int(duration * samplerate), dtype='int16')
        sd.wait()
        write(filename, samplerate, rec)
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

def process_input(audio_file):
    fallback_msg = "Please, do not be shy or hesitant. I am here to listen."

    if not audio_file or not os.path.exists(audio_file) or not is_valid_wav(audio_file):
        tts.speak(fallback_msg, language="english")
        time.sleep(1.2)
        return fallback_msg

    user_input = transcribe_uploaded_audio(audio_file)
    os.remove(audio_file)

    if not user_input or user_input.strip().startswith("❌"):
        tts.speak(fallback_msg, language="english")
        time.sleep(1.2)
        return fallback_msg

    if is_off_topic(user_input):
        warning = "I am here to support your mental and emotional well-being. Let us stay focused on what you are feeling."
        tts.speak(warning, language="english")
        time.sleep(1.2)
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

    tts.speak(response_text, language="english")

    chat_history.append({
        "user": user_input,
        "assistant": response_text,
        "emotion": emotion,
        "language": "english",
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    if should_end_session(user_input):
        goodbye = "I am really glad I could help. Take care of yourself!"
        tts.speak(goodbye, language="english")
        save_chat_history()
        time.sleep(1.2)
        return "🔚 END_SESSION"

    time.sleep(1.2)
    return response_text

# === UI Styling ===
st.markdown("""
<style>
    html, body, [data-testid="stApp"] {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #000, #000);
        color: white !important;
        height: 100vh;
        overflow-x: hidden;
        margin: 0 !important;
        padding: 0 !important;
    }
    .stButton > button {
        background-color: #1a1a1a;
        border: 2px solid #00ffc3;
        color: white;
        font-size: 18px;
        font-weight: bold;
        padding: 14px 30px;
        border-radius: 12px;
        margin-top: 30px;
        box-shadow: 0 0 15px #00ffc3;
        transition: 0.3s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #00ffc3;
        color: #000000;
        box-shadow: 0 0 25px #00ffc3;
    }
    .pulse {
        width: 80px;
        height: 80px;
        background: rgba(0, 255, 195, 0.3);
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        margin: 10px auto;
    }
    @keyframes pulse {
        0% { transform: scale(0.9); opacity: 1; }
        100% { transform: scale(1.2); opacity: 0; }
    }
    #kalp-logo {
        position: fixed;
        top: 0px;
        left: 0px;
        z-index: 9999;
    }
</style>
""", unsafe_allow_html=True)

# === Header UI ===
col1, col2 = st.columns([1, 8])
with col1:
    st.image("logo.png", width=90)
with col2:
    st.image("kalp.gif", use_container_width=True)

# === Logo at Top Left Corner ===
st.markdown("""
<img id='kalp-logo' src='logo.png' width='90'>
""", unsafe_allow_html=True)

# === App Flow ===
if "conversation_active" not in st.session_state:
    st.session_state["conversation_active"] = False

if not st.session_state["conversation_active"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🗣️ Let's start talking"):
        st.session_state["conversation_active"] = True
        st.rerun()

if st.session_state["conversation_active"]:
    st.markdown("<br><div class='pulse'></div><b style='color:#00ffc3;'>🟢 KalpAI is listening... _(Say 'thank you' to end)_</b>", unsafe_allow_html=True)
    with st.spinner("👂🏼 Listening to your voice..."):
        audio_file = record_audio()

    response = process_input(audio_file)

    if response == "🔚 END_SESSION":
        st.session_state["conversation_active"] = False
        st.success("🛑 Conversation ended.")
        st.stop()
    else:
        st.rerun()
