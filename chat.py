import streamlit as st
import os
import pandas as pd

from utils import (
    stream_response,
    speak,
    generate_sermon,
    transcribe_audio,
    get_embedding,
    enforce_format
)

from access_control import enforce_time_access, update_time_used


def chat_page():

    st.title("Ask Pastor Apugo AI")

    enforce_time_access()

    # ================= SESSION =================
    if "chat" not in st.session_state:
        st.session_state.chat = []

    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    if "last_sermon" not in st.session_state:
        st.session_state.last_sermon = None

    # ================= TOP BAR =================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()

    with col2:
        if st.button("🧹 Clear"):
            st.session_state.chat = []
            st.session_state.last_response = None
            st.session_state.last_sermon = None
            st.rerun()

    with col3:
        st.caption(f"👤 {st.session_state.get('username','User')}")

    with col4:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

    # ================= CHAT HISTORY =================
    for role, message in st.session_state.chat:
        with st.chat_message(role):
            st.markdown(message)

    # ================= SERMON =================
    st.subheader("📖 Sermon Generator")

    sermon_topic = st.text_input("Enter sermon topic")

    colS1, colS2, colS3 = st.columns(3)

    # GENERATE
    with colS1:
        if st.button("Generate Sermon") and sermon_topic:

            sermon = generate_sermon(sermon_topic, st.session_state.get("username"))
            sermon = enforce_format(sermon, st.session_state.get("username"))

            clean_sermon = sermon.replace("\n", "\n\n")

            with st.chat_message("assistant"):
                st.markdown(clean_sermon)

            st.session_state.chat.append(("assistant", clean_sermon))
            st.session_state.last_sermon = clean_sermon

            update_time_used(st.session_state.get("username"))

    # SUMMARIZE
    with colS2:
        if st.button("Summarize Sermon") and st.session_state.last_sermon:

            prompt = f"Summarize this sermon in 100 words:\n\n{st.session_state.last_sermon}"

            summary = stream_response(
                [{"role": "user", "content": prompt}],
                st.session_state.get("username"),
                st
            )

            st.markdown("### 📌 Sermon Summary")
            st.markdown(summary)

    # CLEAR SERMON
    with colS3:
        if st.button("Clear Sermon"):
            st.session_state.last_sermon = None
            st.success("Sermon cleared")
            st.rerun()

    st.divider()

    # ================= VOICE =================
    audio = st.audio_input("🎤 Tap and speak")

    typed_input = None

    if audio is not None:
        text = transcribe_audio(audio)
        if text:
            st.success(f"You said: {text}")
            typed_input = text

    # ================= CHAT INPUT =================
    chat_input = st.chat_input("Ask Pastor Apugo AI...")

    if chat_input:
        typed_input = chat_input

    # ================= BUTTONS UNDER INPUT =================
    st.markdown("<br>", unsafe_allow_html=True)

    colA, colB = st.columns(2)

    with colA:
        if st.button("🔄 Refresh", key="refresh_under_input"):
            st.rerun()

    with colB:
        if st.button("🧹 Clear", key="clear_under_input"):
            st.session_state.chat = []
            st.session_state.last_response = None
            st.session_state.last_sermon = None
            st.rerun()

    # ================= PROCESS =================
    if typed_input:

        user_input = typed_input

        st.session_state.chat.append(("user", user_input))

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                try:
                    response = stream_response(
                        [{"role": "user", "content": user_input}],
                        st.session_state.get("username"),
                        st
                    )
                except Exception as e:
                    st.error(f"AI ERROR: {e}")
                    response = "AI failed"

                response = enforce_format(response, st.session_state.get("username"))
                clean_response = response.replace("\n", "\n\n")

                st.markdown(clean_response)

                try:
                    audio_file = speak(response)
                    if audio_file:
                        st.audio(audio_file)
                except:
                    pass

        st.session_state.chat.append(("assistant", clean_response))
        st.session_state.last_response = clean_response

        update_time_used(st.session_state.get("username"))

        # ================= SAVE =================
        try:
            df = pd.read_csv("pending_qa.csv").fillna("")
        except:
            df = pd.DataFrame(columns=[
                "user","question","answer","scripture",
                "category","question_norm","embedding"
            ])

        try:
            embedding = get_embedding(user_input)
        except:
            embedding = ""

        new_row = pd.DataFrame([{
            "user": st.session_state.get("username"),
            "question": user_input,
            "answer": clean_response,
            "scripture": "",
            "category": "",
            "question_norm": user_input.lower(),
            "embedding": embedding
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("pending_qa.csv", index=False)

        st.success("Saved for admin approval")