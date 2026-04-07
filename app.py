import streamlit as st
from auth import auth_page
from chat import chat_page
from admin import admin_page

import pandas as pd
import os

# ================= DEBUG: SHOW WORKING DIRECTORY =================
print("APP RUNNING FROM:", os.getcwd())

# ================= SELF-HEAL FILE SYSTEM =================
def ensure_csv(file, columns):
    try:
        file_path = os.path.abspath(file)
        print(f"Checking file: {file_path}")

        # If file does not exist → create it
        if not os.path.exists(file_path):
            print(f"Creating new file: {file_path}")
            pd.DataFrame(columns=columns).to_csv(file_path, index=False)
            return

        # Try reading file
        df = pd.read_csv(file_path, dtype=str).fillna("")

        # Ensure all required columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = ""

        # Save repaired file
        df.to_csv(file_path, index=False)

    except Exception as e:
        print(f"ERROR with {file}: {e}")
        print(f"Recreating corrupted file: {file}")

        # Recreate file if corrupted
        pd.DataFrame(columns=columns).to_csv(file, index=False)


# ================= ENSURE ALL REQUIRED FILES =================

ensure_csv("invite_codes.csv", ["code","created_by","used_by","status","used"])

ensure_csv("qa_dataset.csv", [
    "user",
    "question",
    "answer",
    "scripture",
    "category",
    "question_norm",
    "embedding"
])

# 🔥 FIXED: pending_qa.csv will ALWAYS be created safely
ensure_csv("pending_qa.csv", [
    "user",
    "question",
    "answer",
    "scripture",
    "category",
    "question_norm",
    "embedding"
])

ensure_csv("usage.csv", ["username","date","count"])

# ✅ TRASH SYSTEM
ensure_csv("deleted_qa.csv", ["question","answer","deleted_at"])


# ================= SESSION INIT =================
if "username" not in st.session_state:
    st.session_state.username = None


# ================= ROUTING =================
if not st.session_state.username:
    auth_page()
else:
    st.sidebar.write(f"👤 {st.session_state.username}")

    # 🔐 ROLE-BASED MENU
    menu = ["Chat"]
    if st.session_state.get("role") == "admin":
        menu.append("Admin")

    choice = st.sidebar.radio("Menu", menu)

    if choice == "Chat":
        chat_page()
    else:
        admin_page()