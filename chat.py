import streamlit as st
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

    # ================= SIDEBAR =================
    with st.sidebar:

        st.markdown("## 👤 User Panel")
        st.write(f"User: {st.session_state.get('username','User')}")

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

        st.markdown("---")

        st.markdown("### 🔐 Change Password")

        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")

        if st.button("Update Password"):
            if new_pw and new_pw == confirm_pw:

                import json
                from auth import hash_pw

                with open("users.json", "r") as f:
                    data = json.load(f)

                for user in data["users"]:
                    if user["username"] == st.session_state.get("username"):
                        user["password"] = hash_pw(new_pw)

                with open("users.json", "w") as f:
                    json.dump(data, f, indent=4)

                st.success("Password updated")
            else:
                st.error("Passwords do not match")

    # ================= SESSION =================
    if "chat" not in st.session_state:
        st.session_state.chat = []

    if "last_sermon" not in st.session_state:
        st.session_state.last_sermon = None

    # ================= CHAT HISTORY =================
    for role, message in st.session_state.chat:
        st.markdown(message)

    # ================= SERMON =================
    st.subheader("📖 Sermon Generator")

    sermon_topic = st.text_input("Enter sermon topic")

    col1, col2, col3 = st.columns(3)

    # Generate
    with col1:
        if st.button("Generate Sermon") and sermon_topic:

            sermon = generate_sermon(sermon_topic, st.session_state.get("username"))
            sermon = enforce_format(sermon, st.session_state.get("username"))

            clean_sermon = sermon.replace("\n", "\n\n")

            st.markdown(clean_sermon)

            st.session_state.chat.append(("assistant", clean_sermon))
            st.session_state.last_sermon = clean_sermon

            update_time_used(st.session_state.get("username"))

    # Word limit selector
    with col2:
        word_limit = st.number_input(
            "Summary length (words)",
            min_value=20,
            max_value=500,
            value=100
        )

    # Summarize
    with col3:
        if st.button("Summarize Sermon") and st.session_state.last_sermon:

            prompt = f"Summarize this sermon in {word_limit} words:\n\n{st.session_state.last_sermon}"

            summary = stream_response(
                [{"role": "user", "content": prompt}],
                st.session_state.get("username"),
                st
            )

            st.markdown("### 📌 Sermon Summary")
            st.markdown(summary)

    st.divider()

    # ================= VOICE =================
    audio = st.audio_input("🎤 Tap and speak")

    typed_input = None

    if audio is not None:
        text = transcribe_audio(audio)
        if text:
            st.success(f"You said: {text}")
            typed_input = text

    # ================= INPUT =================
    chat_input = st.chat_input("Ask Pastor Apugo AI...")

    if chat_input:
        typed_input = chat_input

    # ================= BUTTONS UNDER INPUT =================
    st.markdown("<br>", unsafe_allow_html=True)

    colA, colB = st.columns(2)

    with colA:
        if st.button("🔄 Refresh"):
            st.rerun()

    with colB:
        if st.button("🧹 Clear"):
            st.session_state.chat = []
            st.session_state.last_sermon = None
            st.rerun()

    # ================= PROCESS =================
    if typed_input:

        user_input = typed_input

        st.session_state.chat.append(("user", user_input))
        st.markdown(f"**You:** {user_input}")

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