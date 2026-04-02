import streamlit as st
import json, os
import pandas as pd
from datetime import datetime
import bcrypt

# ================= PASSWORD =================
def hash_pw(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_pw(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

# ================= USERS =================
def load_users():
    if not os.path.exists("users.json"):
        return []
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

# ================= AUTH PAGE =================
def auth_page():

    st.title("ASKPASTORAPUGO AI")

    mode = st.radio("Login / Register", ["Login", "Register"], horizontal=True)

    # 🔥 FORM FIX (CRITICAL)
    with st.form("auth_form"):

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        invite = st.text_input("Invite Code") if mode == "Register" else None

        submitted = st.form_submit_button(mode)

    # ================= PROCESS =================
    if submitted:

        users = load_users()

        # ================= LOGIN =================
        if mode == "Login":

            if not username or not password:
                st.error("Enter username and password")
                return

            for user in users:
                if user["username"] == username and check_pw(password, user["password"]):

                    st.session_state.username = username
                    st.session_state.role = user.get("role", "user")
                    st.session_state.chat = []
                    st.session_state.authenticated = True

                    user["last_login"] = str(datetime.now())
                    save_users(users)

                    st.success("Login successful")
                    st.rerun()

            st.error("Invalid username or password")

        # ================= REGISTER =================
        else:

            if not username or not password:
                st.error("Username and password required")
                return

            # 🚫 Prevent duplicate users
            if any(u["username"] == username for u in users):
                st.error("Username already exists")
                return

            # ================= FIRST USER =================
            if not users:
                users.append({
                    "username": username,
                    "password": hash_pw(password),
                    "role": "admin",
                    "created_at": str(datetime.now()),
                    "last_login": "",
                    "status": "active"
                })

                save_users(users)
                st.success("Admin account created. Please login.")
                return

            # ================= INVITE REQUIRED =================
            if not invite:
                st.error("Invite code required")
                return

            if not os.path.exists("invite_codes.csv"):
                st.error("Invite system missing")
                return

            df = pd.read_csv("invite_codes.csv", dtype=str).fillna("")
            valid = False
            inviter = None

            for i, row in df.iterrows():
                if row["code"].strip() == invite.strip() and row["status"] in ["", "unused"]:

                    valid = True
                    inviter = row["created_by"]

                    df.at[i, "status"] = "used"
                    df.at[i, "used_by"] = username
                    df.to_csv("invite_codes.csv", index=False)

                    break

            if not valid:
                st.error("Invalid invite code")
                return

            # ================= CREATE USER =================
            users.append({
                "username": username,
                "password": hash_pw(password),
                "invite_code": invite,
                "invited_by": inviter,
                "created_at": str(datetime.now()),
                "role": "user",
                "status": "active",
                "last_login": "",
                "total_questions": 0
            })

            save_users(users)
            st.success("Registration successful. Please login.")