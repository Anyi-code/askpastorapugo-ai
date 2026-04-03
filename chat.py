import streamlit as st
from utils import (
    stream_response,
    speak,
    generate_sermon,
    transcribe_audio,
    get_embedding,
    enforce_format
)

# ================= CHAT PAGE =================
def chat_page():

    st.title("Ask Pastor Apugo AI")

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

    # ================= CHAT HISTORY =================
    if "chat" not in st.session_state:
        st.session_state.chat = []

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

                with st.chat_message("assistant"):
                    st.markdown(sermon)

                st.session_state.chat.append(("assistant", sermon))

    with colB:
        if st.button("Clear Sermon"):
            sermon_topic = ""
            st.rerun()

    st.divider()

    # ================= CHAT INPUT =================
    user_input = st.chat_input("Ask Pastor Apugo AI...")

    # ================= MICROPHONE (PLACEHOLDER) =================
    st.caption("🎤 Tap to speak (mobile supported)")

    # ================= SEND MESSAGE =================
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

                st.markdown(response)

                # 🔥 VOICE OUTPUT
                audio_file = speak(response)
                if audio_file:
                    st.audio(audio_file, format="audio/mp3")

        st.session_state.chat.append(("assistant", response))