import streamlit as st
import pandas as pd
import os, json, random, string

from health_dashboard import run_health_dashboard
from access_control import assign_time_to_user


# ================= LOAD DATA =================
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
        st.warning("No users found")

    # ================= TIME CONTROL =================
    st.subheader("⏱ Assign Time")

    if users:
        usernames = [u["username"] for u in users]
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
            "created_by": st.session_state.get("username"),
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
        with open("error_logs.json") as f:
            logs = json.load(f)

        if logs:
            st.dataframe(pd.DataFrame(logs[::-1]), width="stretch")
        else:
            st.success("No errors")

    # ================= PENDING Q&A =================
    st.subheader("⏳ Pending Q&A (Edit → Approve / Reject)")

    pending_file = "pending_qa.csv"
    main_file = "qa_dataset.csv"

    if os.path.exists(pending_file):

        df_pending = pd.read_csv(pending_file).fillna("")
        st.write(f"Rows found: {len(df_pending)}")

        if len(df_pending) > 0:

            for i in range(len(df_pending)):

                row = df_pending.iloc[i]

                st.markdown(f"### Entry {i+1}")
                st.markdown(f"👤 {row['user']}")
                st.markdown(f"**Q:** {row['question']}")

                # ✏️ EDIT FIELDS
                edited_answer = st.text_area(
                    f"Answer {i}",
                    value=row["answer"],
                    key=f"answer_{i}"
                )

                edited_scripture = st.text_input(
                    f"Scripture {i}",
                    value=row["scripture"],
                    key=f"scripture_{i}"
                )

                edited_category = st.text_input(
                    f"Category {i}",
                    value=row["category"],
                    key=f"category_{i}"
                )

                col1, col2 = st.columns(2)

                # ✅ APPROVE
                with col1:
                    if st.button(f"Approve {i}"):

                        new_row = {
                            "user": row["user"],
                            "question": row["question"],
                            "answer": edited_answer,
                            "scripture": edited_scripture,
                            "category": edited_category,
                            "question_norm": row["question"].lower(),
                            "embedding": row.get("embedding", "")
                        }

                        try:
                            df_main = pd.read_csv(main_file)
                        except:
                            df_main = pd.DataFrame(columns=df_pending.columns)

                        df_main = pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True)
                        df_main.to_csv(main_file, index=False)

                        df_pending = df_pending.drop(df_pending.index[i])
                        df_pending.to_csv(pending_file, index=False)

                        st.success("Approved with edits")
                        st.rerun()

                # ❌ REJECT
                with col2:
                    if st.button(f"Reject {i}"):

                        df_pending = df_pending.drop(df_pending.index[i])
                        df_pending.to_csv(pending_file, index=False)

                        st.warning("Rejected")
                        st.rerun()

                st.divider()

        else:
            st.warning("No pending Q&A")

    else:
        st.error("pending_qa.csv not found")

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

    # ================= HEALTH =================
    st.subheader("🧠 System Health")
    run_health_dashboard()