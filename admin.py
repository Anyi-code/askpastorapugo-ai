import streamlit as st
import pandas as pd
import os, json
from checklist import run_checklist
import random, string

# 🔥 NEW IMPORT
from access_control import assign_time_to_user

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

        # 🔥 ENSURE TIME COLUMNS EXIST
        if "time_allocated" not in df_users.columns:
            df_users["time_allocated"] = None

        if "time_used" not in df_users.columns:
            df_users["time_used"] = 0

        # 🔥 CALCULATE REMAINING TIME
        df_users["time_remaining"] = df_users.apply(
            lambda row: (
                round(row["time_allocated"] - row["time_used"], 2)
                if row["time_allocated"] is not None
                else "Unlimited"
            ),
            axis=1
        )

        # 🔥 CLEAN COLUMN ORDER
        display_cols = [
            "username",
            "role",
            "time_allocated",
            "time_used",
            "time_remaining",
            "invite_code_used",
            "invited_by",
            "status",
            "last_login"
        ]

        display_cols = [c for c in display_cols if c in df_users.columns]

        st.dataframe(df_users[display_cols], width="stretch")

    else:
        st.info("No users found")

    # ================= TIME CONTROL =================
    st.subheader("⏱ Assign Time to User (Minutes)")

    if users:
        usernames = [u["username"] for u in users]

        selected_user = st.selectbox("Select User", usernames)
        minutes = st.number_input("Minutes", min_value=1, step=1)

        if st.button("Assign Time"):
            assign_time_to_user(selected_user, minutes)
            st.success(f"{minutes} minutes assigned to {selected_user}")
            st.rerun()

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
        st.dataframe(df_inv, width="stretch")
    else:
        st.info("No invite codes")

    # ================= ERROR LOGS =================
    st.subheader("🚨 Error Logs")

    if os.path.exists("error_logs.json"):
        with open("error_logs.json", "r") as f:
            logs = json.load(f)

        if logs:
            df_logs = pd.DataFrame(logs[::-1])
            st.dataframe(df_logs, width="stretch")
        else:
            st.success("No errors 🎉")
    else:
        st.success("No logs yet 🎉")

    # ================= SYSTEM CHECK =================
    st.subheader("System Health Check")
    run_checklist()