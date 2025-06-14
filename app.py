import os
import json
import streamlit as st
from datetime import datetime
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import wave

from groq_agent import get_groq_llm
from mouth import TextToSpeech
from eye import analyze_emotion
from prompts.system_prompt.system_prompt import system_prompt

# === Init ===
llm = get_groq_llm()
tts = TextToSpeech()
chat_history = []
session_start = datetime.now()

EXIT_PHRASES = {
    "thank you", "thanks", "you solved my problem", "problem solved", "appreciate it", "that helped"
}
OFF_TOPIC_PHRASES = {
    "who is", "tell me about", "what is", "prime minister", "actor", "movie",
    "president", "cricketer", "capital of", "current news", "weather", "joke"
}

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

def record_audio(duration=5, samplerate=44100, filename="temp_audio.wav"):
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
        text = recognizer.recognize_google(audio, language="en-IN")
        return text
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        return f"❌ Error: {e}"

def process_input(audio_file):
    try:
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

        # Run emotion analysis in a separate thread to avoid blocking
        emotion = "neutral"
        thread = Thread(target=lambda: analyze_emotion(text=user_input, use_facial=False), daemon=True)
        thread.start()

        context = system_prompt("neutral")  # Use default emotion to avoid delay
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

    except Exception as e:
        return f"❌ Error: {e}"


# === Streamlit UI ===
st.set_page_config(layout="centered", page_title="Kalp AI")

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
            box-align: center;
        }

        .output-text {
            font-size: 20px;
            color: white;
            margin-top: 40px;
            text-align: center;
        }

        .stCheckbox > div {
            color: white;
            font-size: 16px;
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
        <span style='font-size: 13px;'>🤗 Welcome to KalpAI, your compassionate companion for emotional support and well-being.</span>
    </div>
""", unsafe_allow_html=True)

if st.button("🗣️ Let's start talking"):
    with st.spinner("👂🏼 I'm Listening to you"):
        audio_file = record_audio()
        response = process_input(audio_file)
        st.markdown(f"<div class='output-text'>🤖 {response}</div>", unsafe_allow_html=True)