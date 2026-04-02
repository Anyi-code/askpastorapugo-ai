import streamlit as st
from auth import auth_page
from chat import chat_page
from admin import admin_page

import pandas as pd
import os

# ================= SELF-HEAL FILE SYSTEM =================
def ensure_csv(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)
        return
    
    # Repair missing columns if file exists
    df = pd.read_csv(file, dtype=str).fillna("")
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df.to_csv(file, index=False)

# ================= ENSURE ALL REQUIRED FILES =================

# 🔥 UPDATED: qa_dataset now includes embedding
ensure_csv("invite_codes.csv", ["code","created_by","used_by","status","used"])

ensure_csv("qa_dataset.csv", [
    "user",
    "question",
    "answer",
    "scripture",
    "category",
    "question_norm",
    "embedding"   # 🔥 NEW COLUMN
])

ensure_csv("pending_qa.csv", [
    "user",
    "question",
    "answer",
    "scripture",
    "category",
    "question_norm",
    "embedding"   # 🔥 ALSO ADDED HERE FOR CONSISTENCY
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