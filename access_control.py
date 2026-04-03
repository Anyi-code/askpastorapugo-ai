import streamlit as st
import json
import os
from datetime import datetime

# ================= LOAD USERS =================
def load_users():
    if not os.path.exists("users.json"):
        return {"users": []}
    with open("users.json", "r") as f:
        return json.load(f)

# ================= SAVE USERS =================
def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= START SESSION TIMER =================
def start_timer():
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = datetime.now()

# ================= UPDATE TIME USED =================
def update_time_used(username):

    if "session_start_time" not in st.session_state:
        return

    now = datetime.now()
    elapsed = (now - st.session_state.session_start_time).total_seconds() / 60  # minutes

    data = load_users()

    for user in data["users"]:
        if user["username"] == username:

            used = user.get("time_used", 0)
            user["time_used"] = round(used + elapsed, 2)

            break

    save_users(data)

    # reset timer
    st.session_state.session_start_time = datetime.now()

# ================= CHECK ACCESS =================
def check_time_access(username):

    data = load_users()

    for user in data["users"]:
        if user["username"] == username:

            allocated = user.get("time_allocated", None)
            used = user.get("time_used", 0)

            # No limit → allow
            if allocated is None:
                return True

            if used < allocated:
                return True
            else:
                return False

    return True

# ================= ENFORCE ACCESS =================
def enforce_time_access():

    username = st.session_state.get("username")

    if not username:
        return

    start_timer()

    allowed = check_time_access(username)

    if not allowed:
        st.error("⏰ Your allocated time has finished. Contact admin.")
        st.stop()

# ================= ADMIN: ASSIGN TIME =================
def assign_time_to_user(username, minutes):

    data = load_users()

    for user in data["users"]:
        if user["username"] == username:
            user["time_allocated"] = minutes
            user["time_used"] = 0
            break

    save_users(data)