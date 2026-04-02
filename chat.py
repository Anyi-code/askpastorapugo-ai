import streamlit as st
import time
import os
import pandas as pd
import json
import numpy as np
from filelock import FileLock
from sklearn.metrics.pairwise import cosine_similarity

from utils import stream_response, speak, generate_sermon, transcribe_audio, get_embedding, enforce_format

# ================= MOBILE CSS =================
def inject_mobile_css():
    st.markdown("""
    <style>
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px 10px 20px 10px;
        border-top: 1px solid #eee;
        z-index: 999;
    }
    .main > div {
        padding-bottom: 110px;
    }
    button {
        height: 48px !important;
        font-size: 16px !important;
    }
    input {
        font-size: 16px !important;
    }
    [data-testid="stChatMessage"] {
        margin-bottom: 12px;
    }
    html {
        scroll-behavior: smooth;
    }
    </style>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def is_how(text):
    text = text.lower()
    return any(k in text for k in [
        "how", "ways to", "steps to", "teach me", "help me",
        "guide me", "process of", "method", "strategy"
    ])

def check_rate_limit():
    now = time.time()
    if "last_request" not in st.session_state:
        st.session_state.last_request = 0

    if now - st.session_state.last_request < 2:
        st.warning("Slow down...")
        return False

    st.session_state.last_request = now
    return True

# ================= EMBEDDINGS =================
@st.cache_data
def load_embeddings():
    if not os.path.exists("qa_dataset.csv"):
        return None, None, None

    df = pd.read_csv("qa_dataset.csv").fillna("")
    embeddings = []
    valid_rows = []

    for i, row in df.iterrows():
        try:
            emb = json.loads(row["embedding"])
            embeddings.append(emb)
            valid_rows.append(i)
        except:
            continue

    if not embeddings:
        return df, None, None

    return df, np.array(embeddings), valid_rows

def embedding_search(question):
    df, embeddings_matrix, valid_rows = load_embeddings()

    if embeddings_matrix is None:
        return None

    q_emb = get_embedding(question)
    if q_emb is None:
        return None

    q_emb = np.array(q_emb).reshape(1, -1)
    scores = cosine_similarity(q_emb, embeddings_matrix)[0]

    best_idx = np.argmax(scores)
    best_score = scores[best_idx]

    if best_score > 0.75:
        return df.iloc[valid_rows[best_idx]]["answer"]

    return None

# ================= STRUCTURE ENFORCER =================
def enforce_structure(response, username):
    required_sections = [
        "CORE DEFINITION",
        "SCRIPTURAL AUTHORITY",
        "REVELATION DIMENSIONS",
        "CHRIST CONNECTION",
        "PRACTICAL IMPLICATION",
        "PROPHETIC DECLARATION"
    ]

    missing = [s for s in required_sections if s not in response]

    return missing

# ================= MAIN =================
def chat_page():

    inject_mobile_css()

    st.title("ASKPASTORAPUGO AI")

    # ================= SESSION =================
    if "chat" not in st.session_state:
        st.session_state.chat = []

    if "current_sermon" not in st.session_state:
        st.session_state.current_sermon = None

    if "last_voice_id" not in st.session_state:
        st.session_state.last_voice_id = None

    # ================= SIDEBAR =================
    with st.sidebar:
        st.write(f"👤 {st.session_state.get('username')}")
        st.divider()

        if st.button("🔄 Refresh"):
            st.rerun()

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

        if st.button("Change Password"):
            st.info("Feature coming soon")

    # ================= SERMON =================
    with st.expander("🎤 Sermon Generator", expanded=False):

        topic = st.text_input("Enter sermon topic")

        c1, c2 = st.columns(2)

        if c1.button("Generate Sermon") and topic:
            with st.spinner("Generating sermon..."):
                st.session_state.current_sermon = generate_sermon(
                    topic,
                    st.session_state.get("username", "User")
                )
                st.rerun()

        if c2.button("Clear"):
            st.session_state.current_sermon = None
            st.rerun()

        if st.session_state.current_sermon:
            st.markdown(st.session_state.current_sermon)

            if st.button("🔊 Play"):
                audio = speak(st.session_state.current_sermon)
                if audio:
                    st.audio(audio)

    # ================= CHAT HISTORY =================
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ================= 🎤 MIC =================
    st.markdown("""
    <div style="margin-bottom:6px; font-size:14px; font-weight:500; color:#555;">
    🎤 Tap to speak
    </div>
    """, unsafe_allow_html=True)

    voice_data = st.audio_input("🎤 Speak")

    # ================= CHAT INPUT =================
    user_input = st.chat_input("Ask Pastor Apugo AI...")

    # ================= VOICE =================
    if voice_data is not None and voice_data.size > 0:
        voice_id = f"{voice_data.name}_{voice_data.size}"

        if st.session_state.last_voice_id != voice_id:
            st.session_state.last_voice_id = voice_id

            path = "input.wav"
            with open(path, "wb") as f:
                f.write(voice_data.getbuffer())

            transcript = transcribe_audio(path)
            if transcript:
                user_input = transcript.strip()

    # ================= PROCESS =================
    if user_input:

        if not check_rate_limit():
            return

        if st.session_state.chat and st.session_state.chat[-1]["content"] == user_input:
            return

        username = st.session_state.get("username", "User")

        st.session_state.chat.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state["is_how_mode"] = is_how(user_input)

        # 🔥 FIRST RESPONSE
        dataset_answer = embedding_search(user_input)

        if dataset_answer:
            response = dataset_answer
        else:
            response = stream_response(
                st.session_state.chat,
                username,
                st
            )

        response = enforce_format(response, username)

        # 🔥 STRUCTURE CHECK
        missing = enforce_structure(response, username)

        # 🔥 AUTO RETRY IF INCOMPLETE
        if missing:
            retry_prompt = f"""
Your previous response was incomplete.

You MUST include ALL these sections:

CORE DEFINITION
SCRIPTURAL AUTHORITY
REVELATION DIMENSIONS
CHRIST CONNECTION
PRACTICAL IMPLICATION
PROPHETIC DECLARATION

Rewrite the answer completely.
"""

            response = stream_response(
                [{"role": "system", "content": retry_prompt}] + st.session_state.chat,
                username,
                st
            )

            response = enforce_format(response, username)

        # ================= DISPLAY =================
        with st.chat_message("assistant"):
            placeholder = st.empty()
            typed = ""

            lines = response.split("\n")

            for line in lines:
                typed += line + "\n"
                placeholder.markdown(typed)
                time.sleep(0.05)

        st.session_state.chat.append({"role": "assistant", "content": response})

        # ================= SAVE =================
        embedding = get_embedding(user_input)

        new_entry = pd.DataFrame([[
            username,
            user_input,
            response,
            "", "", user_input.lower(),
            json.dumps(embedding) if embedding else ""
        ]], columns=[
            "user","question","answer","scripture","category","question_norm","embedding"
        ])

        with FileLock("pending_qa.csv.lock"):
            if os.path.exists("pending_qa.csv"):
                df = pd.read_csv("pending_qa.csv")
                df = pd.concat([df, new_entry])
                df.to_csv("pending_qa.csv", index=False)
            else:
                new_entry.to_csv("pending_qa.csv", index=False)