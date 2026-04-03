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
        st.dataframe(df_users, width="stretch")

        usernames = df_users["username"].tolist()
        selected = st.selectbox("View User Details", usernames)

        user_data = next(u for u in users if u["username"] == selected)
        st.json(user_data)
    else:
        st.info("No users found")

    # ================= INVITES =================
    st.subheader("Invite Codes")

    col1, col2 = st.columns(2)

    if col1.button("Generate Code"):
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

        # 🔥 FILTERS
        status_filter = st.selectbox("Filter by status", ["all", "unused", "used"])

        if status_filter != "all":
            df_inv = df_inv[df_inv["status"] == status_filter]

        st.write("Filtered View")
        st.dataframe(df_inv, width="stretch")
    else:
        st.info("No invite codes available")

    # ================= PENDING QA =================
    st.subheader("Pending Q&A")

    if os.path.exists("pending_qa.csv"):
        df = pd.read_csv("pending_qa.csv")

        if df.empty:
            st.info("No pending questions")
        else:
            for i, row in df.iterrows():
                with st.expander(row["question"][:80]):

                    st.write(f"👤 User: {row.get('user','')}")
                    st.write(f"❓ Question: {row['question']}")
                    st.write(f"💬 Answer: {row['answer']}")

                    c1, c2 = st.columns(2)

                    if c1.button("Approve", key=f"approve_{i}"):

                        if os.path.exists("qa_dataset.csv"):
                            main = pd.read_csv("qa_dataset.csv")
                        else:
                            main = pd.DataFrame(columns=df.columns)

                        main = pd.concat([main, pd.DataFrame([row])])
                        main.to_csv("qa_dataset.csv", index=False)

                        df.drop(i, inplace=True)
                        df.to_csv("pending_qa.csv", index=False)

                        st.success("Approved")
                        st.rerun()

                    if c2.button("Reject", key=f"reject_{i}"):

                        df.drop(i, inplace=True)
                        df.to_csv("pending_qa.csv", index=False)

                        st.warning("Rejected")
                        st.rerun()

    # ================= DATASET =================
    st.subheader("Dataset")

    if os.path.exists("qa_dataset.csv"):
        df = pd.read_csv("qa_dataset.csv")

        if df.empty:
            st.info("Dataset is empty")
        else:
            for i, row in df.iterrows():
                with st.expander(row["question"][:80]):

                    new_answer = st.text_area(
                        "Edit Answer",
                        row["answer"],
                        key=f"edit_{i}"
                    )

                    c1, c2 = st.columns(2)

                    if c1.button("Update", key=f"update_{i}"):
                        df.loc[i, "answer"] = new_answer
                        df.to_csv("qa_dataset.csv", index=False)
                        st.success("Updated")
                        st.rerun()

                    if c2.button("Delete", key=f"delete_{i}"):

                        trash = pd.DataFrame([row])
                        trash.to_csv(
                            "deleted_qa.csv",
                            mode='a',
                            header=not os.path.exists("deleted_qa.csv"),
                            index=False
                        )

                        df.drop(i, inplace=True)
                        df.to_csv("qa_dataset.csv", index=False)

                        st.warning("Moved to trash")
                        st.rerun()

    # ================= TRASH =================
    st.subheader("Trash")

    if os.path.exists("deleted_qa.csv"):
        trash = pd.read_csv("deleted_qa.csv")

        if trash.empty:
            st.info("Trash is empty")
        else:
            for i, row in trash.iterrows():
                with st.expander(row["question"][:80]):

                    c1, c2 = st.columns(2)

                    if c1.button("Restore", key=f"restore_{i}"):

                        if os.path.exists("qa_dataset.csv"):
                            main = pd.read_csv("qa_dataset.csv")
                        else:
                            main = pd.DataFrame(columns=trash.columns)

                        main = pd.concat([main, pd.DataFrame([row])])
                        main.to_csv("qa_dataset.csv", index=False)

                        trash.drop(i, inplace=True)
                        trash.to_csv("deleted_qa.csv", index=False)

                        st.success("Restored")
                        st.rerun()

                    if c2.button("Delete Permanently", key=f"perm_{i}"):

                        trash.drop(i, inplace=True)
                        trash.to_csv("deleted_qa.csv", index=False)

                        st.error("Deleted permanently")
                        st.rerun()

    # ================= SYSTEM CHECK =================
    st.subheader("System Health Check")
    run_checklist()