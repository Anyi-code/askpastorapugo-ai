import tempfile
import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# ================= LOAD ENV =================
load_dotenv()


# ================= ERROR LOGGING FIRST (CRITICAL FIX) =================
def send_telegram_alert(message):
    BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
    CHAT_ID = os.getenv("CHAT_ID") or ""

    if not BOT_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        pass


def log_error(username, error, location="unknown"):

    log_file = "error_logs.json"

    log_entry = {
        "username": username or "unknown",
        "error": str(error),
        "location": location,
        "time": str(datetime.now())
    }

    msg = f"""
🚨 ERROR ALERT
User: {log_entry['username']}
Error: {log_entry['error']}
Location: {log_entry['location']}
Time: {log_entry['time']}
"""

    send_telegram_alert(msg)

    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []
    except:
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)

    try:
        if st.session_state.get("role") == "admin":
            st.toast(f"🚨 Error: {error}")
    except:
        pass


# ================= API =================
def get_api_key():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except:
        return os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=get_api_key())


# ================= STREAM RESPONSE =================
def stream_response(messages, username, st_obj=None):

    MASTER_PROMPT = """
YOU ARE ASKPASTORAPUGO_AI — A BIBLE-BASED SCHOLAR, CHRIST-CENTERED, COMPASSIONATE, PROPHETIC TEACHING ASSISTANT.

- Always include scriptures
- Always point to Jesus
- Always end with prophetic declaration
"""

    try:
        messages = [{"role": "system", "content": MASTER_PROMPT}] + messages

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        return response.choices[0].message.content

    except Exception as e:
        log_error(username, e, "stream_response")
        return "An error occurred. Please try again."


# ================= SERMON =================
def generate_sermon(topic, username):

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Generate sermon on {topic}"}]
        )
        return response.choices[0].message.content

    except Exception as e:
        log_error(username, e, "generate_sermon")
        return "Error generating sermon."


# ================= AUDIO =================
def transcribe_audio(audio_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            )

        return transcript.text

    except Exception as e:
        log_error("unknown", e, "transcribe_audio")
        return None


# ================= EMBEDDING =================
def get_embedding(text):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    except Exception as e:
        log_error("system", e, "embedding")
        return None


# ================= FORMAT =================
def enforce_format(response, username):
    if not response.startswith(f"Dear {username}"):
        response = f"Dear {username},\n\n" + response

    if not response.strip().endswith("Remain Blessed"):
        response = response.strip() + "\n\nRemain Blessed"

    return response


# ================= TTS =================
def speak(text):
    try:
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(response.content)
            return f.name

    except Exception as e:
        log_error("system", e, "speak")
        return None