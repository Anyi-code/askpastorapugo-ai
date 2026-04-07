import streamlit as st
import pandas as pd
import os, json
import random, string

# 🔥 NEW HEALTH DASHBOARD
from health_dashboard import run_health_dashboard

# 🔥 TIME CONTROL
from access_control import assign_time_to_user


# ================= LOAD / SAVE =================
def load_data():
    if not os.path.exists("users.json"):
        data = {"users": [], "invites": []}
    else:
        with open("users.json", "r") as f:
            data = json.load(f)

    # AUTO CREATE ADMIN
    if not data.get("users"):
        from auth import hash_pw

        admin_user = {
            "username": "admin",
            "password": hash_pw("admin123"),
            "role": "admin",
            "created_at": "",
            "invite_code_used": "SYSTEM",
            "invited_by": "SYSTEM",
            "status": "active",
            "last_login": "",
            "time_allocated": None,
            "time_used": 0
        }

        data["users"] = [admin_user]

        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

        st.warning("⚠️ Default admin created → username: admin | password: admin123")

    return data


def save_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)


# ================= ADMIN PAGE =================
def admin_page():

    st.title("🛠️ Admin Dashboard")

    data = load_data()
    users = data.get("users", [])
    invites = data.get("invites", [])

    # ================= USERS =================
    st.subheader("👥 Users")

    if users:
        df_users = pd.DataFrame(users)

        if "time_allocated" not in df_users.columns:
            df_users["time_allocated"] = None

        if "time_used" not in df_users.columns:
            df_users["time_used"] = 0

        df_users["time_remaining"] = df_users.apply(
            lambda row: (
                round(row["time_allocated"] - row["time_used"], 2)
                if row["time_allocated"] is not None
                else "Unlimited"
            ),
            axis=1
        )

        st.dataframe(df_users, width="stretch")

    else:
        st.warning("⚠️ No users found.")

    # ================= TIME CONTROL =================
    st.subheader("⏱ Assign Time")

    if users:
        usernames = [u.get("username") for u in users]

        selected_user = st.selectbox("Select User", usernames)
        minutes = st.number_input("Minutes", min_value=1)

        if st.button("Assign Time"):
            assign_time_to_user(selected_user, minutes)
            st.success(f"{minutes} mins assigned")
            st.rerun()

    # ================= INVITES =================
    st.subheader("🎟️ Invite Codes")

    if st.button("Generate Code"):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        invites.append({
            "code": code,
            "created_by": st.session_state.get("username", "admin"),
            "used_by": "",
            "status": "unused"
        })

        save_data(data)
        st.success(f"Code: {code}")
        st.rerun()

    if invites:
        st.dataframe(pd.DataFrame(invites), width="stretch")

    # ================= ERROR LOGS =================
    st.subheader("🚨 Error Logs")

    if os.path.exists("error_logs.json"):
        with open("error_logs.json", "r") as f:
            logs = json.load(f)

        if logs:
            st.dataframe(pd.DataFrame(logs[::-1]), width="stretch")
        else:
            st.success("No errors")

    # ================= PENDING Q&A =================
    st.subheader("⏳ Pending Q&A (Approve / Reject)")

    pending_file = "pending_qa.csv"
    main_file = "qa_dataset.csv"

    if os.path.exists(pending_file):

        df_pending = pd.read_csv(pending_file, engine="python")
        df_pending.columns = df_pending.columns.str.strip()

        st.write(f"Rows found: {len(df_pending)}")

        if len(df_pending) > 0:

            for i in range(len(df_pending)):

                row = df_pending.iloc[i]

                st.markdown(f"### 🔹 Entry {i+1}")
                st.markdown(f"**👤 User:** {row['user']}")
                st.markdown(f"**Q:** {row['question']}")
                st.markdown(f"**A:** {row['answer']}")
                st.markdown(f"**📖 Scripture:** {row['scripture']}")
                st.markdown(f"**📂 Category:** {row['category']}")

                col1, col2 = st.columns(2)

                # APPROVE
                with col1:
                    if st.button(f"Approve {i}", key=f"approve_{i}"):

                        if os.path.exists(main_file):
                            df_main = pd.read_csv(main_file, engine="python")
                        else:
                            df_main = pd.DataFrame(columns=df_pending.columns)

                        df_main = pd.concat([df_main, pd.DataFrame([row])], ignore_index=True)
                        df_main.to_csv(main_file, index=False)

                        df_pending = df_pending.drop(df_pending.index[i])
                        df_pending.to_csv(pending_file, index=False)

                        st.success("Approved")
                        st.rerun()

                # REJECT
                with col2:
                    if st.button(f"Reject {i}", key=f"reject_{i}"):

                        df_pending = df_pending.drop(df_pending.index[i])
                        df_pending.to_csv(pending_file, index=False)

                        st.warning("Rejected")
                        st.rerun()

                st.divider()

        else:
            st.warning("No pending Q&A")

    else:
        st.error("pending_qa.csv not found")

    # ================= HEALTH DASHBOARD =================
    st.subheader("🧠 System Health Dashboard")
    run_health_dashboard()