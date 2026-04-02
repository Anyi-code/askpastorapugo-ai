import streamlit as st
import os

def run_checklist():

    st.subheader("🧪 System Checklist")

    checks = {
        "Authentication": [
            "Login/Register toggle visible",
            "User can login",
            "User can register with invite code",
        ],

        "Chat System": [
            "Chat input box working",
            "Streaming response working",
            "Chat history persists",
            "Microphone button visible",
            "Voice output plays fully",
        ],

        "AI Behavior": [
            "Master prompt enforced",
            "Scripture included in answers",
            "Prophetic tone present",
            "Auto prayer for 'how' questions",
            "Sermon generator working",
        ],

        "Admin Panel": [
            "Admin dashboard loads",
            "User search works",
            "Invite code generation works",
        ],

        "Dataset Control": [
            "Dataset loads correctly",
            "Edit answer works",
            "Update button works",
            "Delete moves to trash",
        ],

        "Pending Q&A": [
            "Pending QA loads",
            "Approve button works",
            "Reject button works",
        ],

        "Trash System": [
            "Trash loads",
            "Restore works",
            "Permanent delete works",
        ],

        "System Files": [
            "users.json exists",
            "invite_codes.csv exists",
            "qa_dataset.csv exists",
            "pending_qa.csv exists",
            "deleted_qa.csv exists",
        ]
    }

    all_ok = True

    # UI checklist
    for section, items in checks.items():
        st.markdown(f"### 🔹 {section}")

        for item in items:
            status = st.checkbox(item, key=item)

            if not status:
                all_ok = False

    st.divider()

    # 🔍 Automatic file checks
    st.markdown("### 🔍 Automatic File Check")

    required_files = [
        "users.json",
        "invite_codes.csv",
        "qa_dataset.csv",
        "pending_qa.csv",
        "deleted_qa.csv"
    ]

    for file in required_files:
        if os.path.exists(file):
            st.success(f"✔ {file} found")
        else:
            st.error(f"❌ {file} missing")
            all_ok = False

    st.divider()

    # FINAL STATUS
    if all_ok:
        st.success("🔥 ALL SYSTEMS FULLY OPERATIONAL")
    else:
        st.warning("⚠️ Some features need attention — review checklist above")