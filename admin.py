import streamlit as st
import pandas as pd
import os
import json
import random
import string


def admin_page():

    st.title("🛠️ Admin Dashboard")

    # ================= USERS =================
    if os.path.exists("users.json"):
        with open("users.json") as f:
            data = json.load(f)

        st.subheader("👥 Users")
        st.dataframe(pd.DataFrame(data.get("users", [])))

    # ================= INVITES =================
    st.subheader("🎟️ Invite Codes")

    if st.button("Generate Code"):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        data["invites"].append({
            "code": code,
            "created_by": st.session_state.get("username"),
            "used_by": "",
            "status": "unused"
        })

        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

        st.success(code)

    if data.get("invites"):
        st.dataframe(pd.DataFrame(data["invites"]))

    # ================= PENDING =================
    st.subheader("⏳ Pending Q&A")

    if os.path.exists("pending_qa.csv"):

        df = pd.read_csv("pending_qa.csv").fillna("")

        for i, row in df.iterrows():

            st.markdown(f"### Entry {i+1}")
            st.write(row["question"])

            answer = st.text_area("Answer", row["answer"], key=f"a{i}")
            scripture = st.text_input("Scripture", row["scripture"], key=f"s{i}")
            category = st.text_input("Category", row["category"], key=f"c{i}")

            col1, col2 = st.columns(2)

            # APPROVE
            with col1:
                if st.button("Approve", key=f"ap{i}"):

                    try:
                        main = pd.read_csv("qa_dataset.csv")
                    except:
                        main = pd.DataFrame(columns=df.columns)

                    new = pd.DataFrame([{
                        "user": row["user"],
                        "question": row["question"],
                        "answer": answer,
                        "scripture": scripture,
                        "category": category,
                        "question_norm": row["question"].lower(),
                        "embedding": row.get("embedding", "")
                    }])

                    main = pd.concat([main, new], ignore_index=True)
                    main.to_csv("qa_dataset.csv", index=False)

                    df = df.drop(i)
                    df.to_csv("pending_qa.csv", index=False)

                    st.success("Approved")
                    st.rerun()

            # REJECT
            with col2:
                if st.button("Reject", key=f"r{i}"):

                    df = df.drop(i)
                    df.to_csv("pending_qa.csv", index=False)

                    st.warning("Rejected")
                    st.rerun()

            st.divider()

    else:
        st.warning("No pending Q&A")

    # ================= ADMIN CHAT =================
    st.subheader("💬 Admin Chat")

    st.chat_input("Admin message...")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()

    with col2:
        if st.button("🧹 Clear"):
            st.session_state.chat = []
            st.rerun()