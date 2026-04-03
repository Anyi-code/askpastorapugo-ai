import streamlit as st
import json
import os
from datetime import datetime
import bcrypt
from utils import log_error

# ================= ENV CHECK =================
def is_cloud():
    return os.getenv("STREAMLIT_SHARING_MODE") is not None

# ================= PASSWORD =================
def hash_pw(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_pw(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

# ================= LOAD / SAVE =================
def load_data():
    if not os.path.exists("users.json"):
        return {"users": [], "invites": []}
    with open("users.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= AUTH PAGE =================
def auth_page():

    st.title("ASKPASTORAPUGO AI")

    # 🔥 CLOUD-ONLY (ADMIN LOCAL ALLOWED)
    # 🔥 TEMPORARY: DISABLE CLOUD CHECK (FIX ISSUE)
    # (You can re-enable later when stable)
    pass

    mode = st.radio("Login / Register", ["Login", "Register"], horizontal=True)

    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        invite = st.text_input("Invite Code") if mode == "Register" else None
        submitted = st.form_submit_button(mode)

    if submitted:

        data = load_data()
        users = data["users"]
        invites = data["invites"]

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
                    save_data(data)

                    st.success("Login successful")
                    st.rerun()

            st.error("Invalid username or password")
            log_error(username, "Login failed", "auth.py")

        # ================= REGISTER =================
        else:

            if not username or not password:
                st.error("Username and password required")
                return

            if any(u["username"] == username for u in users):
                st.error("Username already exists")
                return

            if invite:
                invite = invite.strip().upper()

            # FIRST USER → ADMIN
            if not users:
                users.append({
                    "username": username,
                    "password": hash_pw(password),
                    "role": "admin",
                    "created_at": str(datetime.now()),
                    "invite_code_used": "ADMIN",
                    "invited_by": "system",
                    "status": "active",
                    "last_login": ""
                })
                save_data(data)
                st.success("Admin account created. Please login.")
                return

            if not invite:
                st.error("Invite code required")
                return

            valid_index = None

            for i, inv in enumerate(invites):
                code_db = str(inv.get("code", "")).strip().upper()
                status = str(inv.get("status", "")).strip().lower()

                if code_db == invite and status == "unused":
                    valid_index = i
                    break

            if valid_index is None:
                st.error("Invalid invite code")
                log_error(username, "Invalid invite code", "auth.py")
                return

            inviter = invites[valid_index]["created_by"]

            invites[valid_index]["status"] = "used"
            invites[valid_index]["used_by"] = username

            users.append({
                "username": username,
                "password": hash_pw(password),
                "role": "user",
                "created_at": str(datetime.now()),
                "invite_code_used": invite,
                "invited_by": inviter,
                "status": "active",
                "last_login": ""
            })

            save_data(data)

            st.success("Registration successful. Please login.")