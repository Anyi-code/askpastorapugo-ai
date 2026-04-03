import os
import json
import requests
from datetime import datetime
import streamlit as st

# ================= API KEY =================
def get_api_key():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except:
        return None

# ================= TELEGRAM ALERT =================
def send_telegram_alert(message):
    BOT_TOKEN = "8609344390:AAEKRxKl220-RPPmSzjtlpVCRmjaZQgUwD8"
    CHAT_ID = "1380080803"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload)
    except:
        pass

# ================= ERROR LOGGING =================
def log_error(username, error, location="unknown"):

    log_file = "error_logs.json"

    log_entry = {
        "username": username or "unknown",
        "error": str(error),
        "location": location,
        "time": str(datetime.now())
    }

    # 🔥 SEND TELEGRAM ALERT
    msg = f"""
🚨 ERROR ALERT
User: {log_entry['username']}
Error: {log_entry['error']}
Location: {log_entry['location']}
Time: {log_entry['time']}
"""

    send_telegram_alert(msg)

    # 🔥 SAVE TO FILE
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                logs = json.load(f)
            except:
                logs = []
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)

    # 🔥 ADMIN REAL-TIME TOAST
    if st.session_state.get("role") == "admin":
        st.toast(f"🚨 Error: {error}")