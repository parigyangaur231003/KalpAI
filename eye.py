import cv2
import time
from nrclex import NRCLex
from deepface import DeepFace
import warnings

warnings.filterwarnings("ignore")

# ==========================
# Text Emotion Analysis
# ==========================

def analyze_text_emotion(text: str) -> str:
    """
    Analyze emotion from text using NRCLex.
    Returns the most dominant emotion or 'neutral' if undetected.
    """
    try:
        emotion_obj = NRCLex(text)
        scores = emotion_obj.raw_emotion_scores

        if not scores:
            return "neutral"

        dominant_emotion = max(scores.items(), key=lambda x: x[1])[0]
        print(f"📝 Text Emotion: {dominant_emotion}")
        return dominant_emotion

    except Exception as e:
        print(f"❌ Text emotion analysis error: {e}")
        return "neutral"

# ==========================
# Facial Emotion Analysis
# ==========================

def analyze_facial_emotion(frames_to_capture: int = 5) -> str:
    """
    Analyze facial emotion using DeepFace across multiple frames.
    Returns the most frequently detected emotion.
    """
    print("📸 Capturing facial emotion...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not access webcam.")
        return "neutral"

    emotions = []

    for _ in range(frames_to_capture):
        ret, frame = cap.read()
        if not ret:
            continue

        try:
            result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)

            emotion = result[0]["dominant_emotion"] if isinstance(result, list) else result["dominant_emotion"]
            print(f"🙂 Frame emotion: {emotion}")
            emotions.append(emotion.lower())
        except Exception as e:
            print(f"❌ DeepFace error: {e}")
        time.sleep(0.2)

    cap.release()

    if not emotions:
        return "neutral"

    # Most common emotion
    final_emotion = max(set(emotions), key=emotions.count)
    print(f"🧠 Final Facial Emotion: {final_emotion}")
    return final_emotion

# ==========================
# Combined Emotion Decision
# ==========================

def analyze_emotion(text: str = None, use_facial: bool = True) -> str:
    """
    Analyze emotion from text and optionally facial expression.
    Returns the most severe (prioritized) emotion.
    """
    emotions = []

    if text:
        emotions.append(analyze_text_emotion(text))

    if use_facial:
        emotions.append(analyze_facial_emotion())

    if not emotions:
        return "neutral"

    # Define severity: higher number = higher concern
    emotion_weights = {
        "anger": 5,
        "fear": 4,
        "sadness": 4,
        "disgust": 4,
        "neutral": 3,
        "trust": 2,
        "content": 2,
        "happy": 1,
        "joy": 1,
        "surprise": 2
    }

    final_emotion = max(emotions, key=lambda e: emotion_weights.get(e.lower(), 0))
    print(f"🧠 Final Combined Emotion: {final_emotion}")
    return final_emotion

# ==========================
# Quick Test
# ==========================

if __name__ == "__main__":
    sample_text = "I feel anxious and nervous about the result."
    emotion = analyze_emotion(sample_text, use_facial=True)
    print("🎯 Emotion Result:", emotion)