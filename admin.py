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

    # 🔥 AUTO CREATE ADMIN IF EMPTY
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

        st.dataframe(df_users[display_cols], use_container_width=True)

    else:
        st.warning("⚠️ No users found. Register users first.")

    # ================= TIME CONTROL =================
    st.subheader("⏱ Assign Time to User (Minutes)")

    if users:
        usernames = [u.get("username", "unknown") for u in users]

        selected_user = st.selectbox("Select User", usernames)
        minutes = st.number_input("Minutes", min_value=1, step=1)

        if st.button("Assign Time"):
            assign_time_to_user(selected_user, minutes)
            st.success(f"{minutes} minutes assigned to {selected_user}")
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

    # ================= PENDING Q&A =================
    st.subheader("⏳ Pending Q&A (Approve / Reject)")

    pending_file = "pending_qa.csv"
    main_file = "qa_dataset.csv"

    if os.path.exists(pending_file):

        try:
            df_pending = pd.read_csv(pending_file, engine="python")
            df_pending.columns = df_pending.columns.str.strip()

            st.write("Rows found:", len(df_pending))  # debug

        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            df_pending = pd.DataFrame()

        if not df_pending.empty:

            for i, row in df_pending.iterrows():

                st.markdown(f"**👤 User:** {row.get('user','')}")
                st.markdown(f"**Q:** {row.get('question','')}")
                st.markdown(f"**A:** {row.get('answer','')}")
                st.markdown(f"**📖 Scripture:** {row.get('scripture','')}")
                st.markdown(f"**📂 Category:** {row.get('category','')}")

                col1, col2 = st.columns(2)

                # APPROVE
                with col1:
                    if st.button(f"✅ Approve {i}", key=f"approve_{i}"):

                        if os.path.exists(main_file):
                            df_main = pd.read_csv(main_file, engine="python")
                        else:
                            df_main = pd.DataFrame(columns=df_pending.columns)

                        df_main = pd.concat([df_main, pd.DataFrame([row])], ignore_index=True)
                        df_main.to_csv(main_file, index=False)

                        df_pending = df_pending.drop(i)
                        df_pending.to_csv(pending_file, index=False)

                        st.success("Approved and moved to dataset")
                        st.rerun()

                # REJECT
                with col2:
                    if st.button(f"❌ Reject {i}", key=f"reject_{i}"):

                        df_pending = df_pending.drop(i)
                        df_pending.to_csv(pending_file, index=False)

                        st.warning("Rejected and removed")
                        st.rerun()

                st.divider()

        else:
            st.warning("⚠️ File loaded but empty")

    else:
        st.error("❌ pending_qa.csv NOT FOUND")

    # ================= SYSTEM HEALTH =================
    st.subheader("🧠 System Health Dashboard")
    run_health_dashboard()