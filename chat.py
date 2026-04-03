import streamlit as st
from utils import (
    stream_response,
    speak,
    generate_sermon,
    transcribe_audio,
    get_embedding,
    enforce_format
)

def chat_page():

    st.title("Ask Pastor Apugo AI")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    # DISPLAY CHAT
    for role, message in st.session_state.chat:
        with st.chat_message(role):
            st.markdown(message)

    # INPUT
    user_input = st.chat_input("Ask Pastor Apugo AI...")

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