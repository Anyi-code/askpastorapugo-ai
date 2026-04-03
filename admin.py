import streamlit as st
import pandas as pd
import os, json
from checklist import run_checklist
import random, string

# ================= LOAD / SAVE =================
def load_data():
    if not os.path.exists("users.json"):
        return {"users": [], "invites": []}
    with open("users.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= ADMIN PAGE =================
def admin_page():

    st.title("Admin Dashboard")

    data = load_data()
    users = data.get("users", [])
    invites = data.get("invites", [])

    # ================= USERS =================
    st.subheader("Users")

    if users:
        df_users = pd.DataFrame(users)
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("No users found")

    # ================= INVITES =================
    st.subheader("Invite Codes")

    if st.button("Generate Code"):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        invites.append({
            "code": code,
            "created_by": st.session_state.get("username", "admin"),
            "used_by": "",
            "status": "unused"
        })

        save_data(data)
        st.success(f"Code generated: {code}")
        st.rerun()

    if invites:
        df_inv = pd.DataFrame(invites)
        st.dataframe(df_inv, use_container_width=True)
    else:
        st.info("No invite codes")

    # ================= ERROR LOGS =================
    st.subheader("🚨 Error Logs")

    if os.path.exists("error_logs.json"):
        with open("error_logs.json", "r") as f:
            logs = json.load(f)

        if logs:
            df_logs = pd.DataFrame(logs[::-1])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.success("No errors 🎉")
    else:
        st.success("No logs yet 🎉")

    # ================= SYSTEM CHECK =================
    st.subheader("System Health Check")
    run_checklist()