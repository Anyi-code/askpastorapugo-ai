import streamlit as st
import json

from utils import (
    stream_response,
    speak,
    generate_sermon,
    transcribe_audio,
    get_embedding,
    enforce_format
)

# 🔥 NEW IMPORT
from access_control import enforce_time_access, update_time_used

# ================= CHAT PAGE =================
def chat_page():

    st.title("Ask Pastor Apugo AI")

    # 🔥 ENFORCE TIME ACCESS
    enforce_time_access()

    # ================= SESSION INIT =================
    if "chat" not in st.session_state:
        st.session_state.chat = []

    # ================= TOP BAR =================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()

    with col2:
        if st.button("🧹 Clear"):
            st.session_state.chat = []
            st.rerun()

    with col3:
        st.caption(f"👤 {st.session_state.get('username','User')}")

    with col4:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

    # ================= PASSWORD CHANGE =================
    with st.expander("🔐 Change Password"):
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")

        if st.button("Update Password"):
            if new_pw and new_pw == confirm_pw:

                with open("users.json", "r") as f:
                    data = json.load(f)

                for user in data["users"]:
                    if user["username"] == st.session_state["username"]:
                        from auth import hash_pw
                        user["password"] = hash_pw(new_pw)

                with open("users.json", "w") as f:
                    json.dump(data, f, indent=4)

                st.success("Password updated successfully")
            else:
                st.error("Passwords do not match")

    # ================= CHAT HISTORY =================
    for role, message in st.session_state.chat:
        with st.chat_message(role):
            st.markdown(message)

    # ================= SERMON GENERATOR =================
    st.subheader("📖 Sermon Generator")

    sermon_topic = st.text_input("Enter sermon topic")

    colA, colB = st.columns(2)

    with colA:
        if st.button("Generate Sermon"):
            if sermon_topic:

                sermon = generate_sermon(
                    sermon_topic,
                    st.session_state.get("username", "User")
                )

                sermon = enforce_format(
                    sermon,
                    st.session_state.get("username", "User")
                )

                clean_sermon = sermon.replace("\n", "\n\n")

                with st.chat_message("assistant"):
                    st.markdown(clean_sermon)

                st.session_state.chat.append(("assistant", clean_sermon))

                # 🔥 UPDATE TIME
                update_time_used(st.session_state.get("username"))

    with colB:
        if st.button("Clear Sermon"):
            st.rerun()

    st.divider()

    # ================= MICROPHONE =================
    st.caption("🎤 Tap to speak (mobile supported)")

    audio = st.audio_input("🎤 Tap and speak")

    user_input = None

    if audio is not None:
        with st.spinner("Listening..."):
            text = transcribe_audio(audio)

        if text:
            st.success(f"You said: {text}")
            user_input = text

    # ================= TEXT INPUT =================
    typed_input = st.chat_input("Ask Pastor Apugo AI...")

    if typed_input:
        user_input = typed_input

    # ================= PROCESS MESSAGE =================
    if user_input:

        st.session_state.chat.append(("user", user_input))

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                response = stream_response(
                    [{"role": "user", "content": user_input}],
                    st.session_state.get("username", "User"),
                    st
                )

                response = enforce_format(
                    response,
                    st.session_state.get("username", "User")
                )

                clean_response = response.replace("\n", "\n\n")

                st.markdown(clean_response)

                # ================= VOICE =================
                audio_file = speak(response)
                if audio_file:
                    st.audio(audio_file, format="audio/mp3")

        st.session_state.chat.append(("assistant", clean_response))

        # 🔥 UPDATE TIME AFTER RESPONSE
        update_time_used(st.session_state.get("username"))