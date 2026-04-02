import streamlit as st
import pandas as pd
import os, json
from filelock import FileLock
from checklist import run_checklist

# ================= ADMIN VERIFICATION =================
def verify_admin():
    if not os.path.exists("users.json"):
        return False

    users = json.load(open("users.json"))

    for u in users:
        if u["username"] == st.session_state.get("username") and u.get("role") == "admin":
            return True

    return False

# ================= ADMIN PAGE =================
def admin_page():

    # 🔒 HARD LOCK
    if not st.session_state.get("authenticated") or not verify_admin():
        st.error("Unauthorized access")
        st.stop()

    st.title("Admin Dashboard")

    # ================= USERS =================
    st.subheader("Users")

    if os.path.exists("users.json"):
        users = json.load(open("users.json"))
        names = [u["username"] for u in users]

        selected = st.selectbox("Search user", names)
        st.write(next(u for u in users if u["username"] == selected))

    # ================= INVITES =================
    st.subheader("Invite Codes")

    if st.button("Generate Code"):
        import random, string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        df = pd.DataFrame([[code, "admin", "", "unused"]],
                          columns=["code","created_by","used_by","status"])

        with FileLock("invite_codes.csv.lock"):
            df.to_csv("invite_codes.csv",
                      mode='a',
                      header=not os.path.exists("invite_codes.csv"),
                      index=False)

        st.success(f"Code Generated: {code}")

    if os.path.exists("invite_codes.csv"):
        st.dataframe(pd.read_csv("invite_codes.csv"))

    # ================= PENDING QA =================
    st.subheader("Pending Q&A")

    if os.path.exists("pending_qa.csv"):
        df = pd.read_csv("pending_qa.csv").fillna("")

        if df.empty:
            st.info("No pending questions")
        else:
            for i, row in df.iterrows():

                question = str(row.get("question", ""))
                answer = str(row.get("answer", ""))
                user = str(row.get("user", ""))
                category = str(row.get("category", ""))
                scripture = str(row.get("scripture", ""))

                with st.expander(question[:80]):

                    st.markdown(f"**User:** {user}")
                    if category:
                        st.markdown(f"**Category:** {category}")
                    if scripture:
                        st.markdown(f"**Scripture:** {scripture}")

                    st.markdown("**Answer:**")
                    st.write(answer)

                    c1, c2 = st.columns(2)

                    # ✅ APPROVE
                    if c1.button("Approve", key=f"approve_{i}"):

                        with FileLock("qa_dataset.csv.lock"):
                            if os.path.exists("qa_dataset.csv"):
                                main = pd.read_csv("qa_dataset.csv").fillna("")
                            else:
                                main = pd.DataFrame(columns=df.columns)

                            main = pd.concat([main, pd.DataFrame([row])])
                            main.to_csv("qa_dataset.csv", index=False)

                        with FileLock("pending_qa.csv.lock"):
                            df.drop(i, inplace=True)
                            df.to_csv("pending_qa.csv", index=False)

                        st.success("Approved and added to dataset")
                        st.rerun()

                    # ❌ REJECT
                    if c2.button("Reject", key=f"reject_{i}"):

                        with FileLock("pending_qa.csv.lock"):
                            df.drop(i, inplace=True)
                            df.to_csv("pending_qa.csv", index=False)

                        st.warning("Rejected")
                        st.rerun()

    # ================= DATASET =================
    st.subheader("Dataset")

    if os.path.exists("qa_dataset.csv"):
        df = pd.read_csv("qa_dataset.csv").fillna("")

        for i, row in df.iterrows():

            question = str(row.get("question", ""))
            answer = str(row.get("answer", ""))

            with st.expander(question[:80]):

                new_answer = st.text_area("Edit Answer", answer, key=f"edit_{i}")

                c1, c2 = st.columns(2)

                # ✏️ UPDATE
                if c1.button("Update", key=f"update_{i}"):

                    with FileLock("qa_dataset.csv.lock"):
                        df.loc[i, "answer"] = new_answer
                        df.to_csv("qa_dataset.csv", index=False)

                    st.success("Updated")
                    st.rerun()

                # 🗑️ DELETE → TRASH
                if c2.button("Delete", key=f"delete_{i}"):

                    trash_row = pd.DataFrame([row])

                    with FileLock("deleted_qa.csv.lock"):
                        trash_row.to_csv("deleted_qa.csv",
                                         mode='a',
                                         header=not os.path.exists("deleted_qa.csv"),
                                         index=False)

                    with FileLock("qa_dataset.csv.lock"):
                        df.drop(i, inplace=True)
                        df.to_csv("qa_dataset.csv", index=False)

                    st.warning("Moved to Trash")
                    st.rerun()

    # ================= TRASH =================
    st.subheader("Trash")

    if os.path.exists("deleted_qa.csv"):
        trash = pd.read_csv("deleted_qa.csv").fillna("")

        for i, row in trash.iterrows():

            question = str(row.get("question", ""))

            with st.expander(question[:80]):

                c1, c2 = st.columns(2)

                # 🔄 RESTORE
                if c1.button("Restore", key=f"restore_{i}"):

                    with FileLock("qa_dataset.csv.lock"):
                        main = pd.read_csv("qa_dataset.csv").fillna("")
                        main = pd.concat([main, pd.DataFrame([row])])
                        main.to_csv("qa_dataset.csv", index=False)

                    with FileLock("deleted_qa.csv.lock"):
                        trash.drop(i, inplace=True)
                        trash.to_csv("deleted_qa.csv", index=False)

                    st.success("Restored")
                    st.rerun()

                # ❌ DELETE PERMANENTLY
                if c2.button("Delete Permanently", key=f"perm_{i}"):

                    with FileLock("deleted_qa.csv.lock"):
                        trash.drop(i, inplace=True)
                        trash.to_csv("deleted_qa.csv", index=False)

                    st.error("Deleted permanently")
                    st.rerun()

    # ================= SYSTEM CHECK =================
    st.subheader("System Health Check")
    run_checklist()