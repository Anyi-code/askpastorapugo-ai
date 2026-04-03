import streamlit as st
import os
import pandas as pd
import shutil
import json
from datetime import datetime
import glob

LATEST_BACKUP_FILE = "backups/latest_backup.json"


# ===============================
# STATUS DISPLAY
# ===============================
def status_display(status, message):
    if status == "good":
        st.success(f"🟢 {message}")
        return 1
    elif status == "warning":
        st.warning(f"🟡 {message}")
        return 0.5
    else:
        st.error(f"🔴 {message}")
        return 0


# ===============================
# CHECK FUNCTIONS
# ===============================
def check_file(filepath):
    if os.path.exists(filepath):
        return "good", f"{filepath} exists"
    else:
        return "bad", f"{filepath} missing"


def check_csv(filepath):
    if not os.path.exists(filepath):
        return "bad", f"{filepath} missing"

    try:
        df = pd.read_csv(filepath)

        if df.empty:
            return "warning", f"{filepath} is empty"

        return "good", f"{filepath} loaded ({len(df)} rows)"

    except Exception as e:
        return "bad", f"{filepath} error: {e}"


# ===============================
# BACKUP SYSTEM
# ===============================
def backup_file(filepath):
    if not os.path.exists(filepath):
        return

    os.makedirs("backups", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(filepath)

    backup_path = f"backups/{timestamp}_{filename}"

    shutil.copy(filepath, backup_path)

    latest = {}

    if os.path.exists(LATEST_BACKUP_FILE):
        with open(LATEST_BACKUP_FILE, "r") as f:
            latest = json.load(f)

    latest[filepath] = backup_path

    with open(LATEST_BACKUP_FILE, "w") as f:
        json.dump(latest, f, indent=4)


# ===============================
# RESTORE LAST (UNDO)
# ===============================
def restore_last_backup(filepath):
    if not os.path.exists(LATEST_BACKUP_FILE):
        return False, "No backup record found"

    with open(LATEST_BACKUP_FILE, "r") as f:
        latest = json.load(f)

    if filepath not in latest:
        return False, "No backup available"

    backup_path = latest[filepath]

    if not os.path.exists(backup_path):
        return False, "Backup file missing"

    shutil.copy(backup_path, filepath)

    return True, f"{filepath} restored successfully"


# ===============================
# FIX FUNCTIONS (SAFE)
# ===============================
def create_file(filepath):
    backup_file(filepath)

    if filepath.endswith(".csv"):
        pd.DataFrame({"question": [], "answer": []}).to_csv(filepath, index=False)
    else:
        with open(filepath, "w") as f:
            f.write("{}")


def fix_csv(filepath):
    backup_file(filepath)
    pd.DataFrame({"question": [], "answer": []}).to_csv(filepath, index=False)


def reset_logs():
    backup_file("error_logs.json")
    with open("error_logs.json", "w") as f:
        f.write("[]")


# ===============================
# BACKUP MANAGER UI
# ===============================
def backup_manager_ui():
    st.subheader("📦 Backup Manager")

    if not os.path.exists("backups"):
        st.info("No backups yet")
        return

    backup_files = glob.glob("backups/*")

    if not backup_files:
        st.info("No backup files found")
        return

    grouped = {}

    for file in backup_files:
        name = os.path.basename(file)
        parts = name.split("_", 2)

        if len(parts) >= 3:
            original = parts[2]
        else:
            original = name

        grouped.setdefault(original, []).append(file)

    for original_file, files in grouped.items():
        st.markdown(f"### 📄 {original_file}")

        selected = st.selectbox(
            f"Select backup for {original_file}",
            files,
            key=original_file
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"Restore {original_file}", key=f"restore_{original_file}"):
                try:
                    shutil.copy(selected, original_file)
                    st.success(f"{original_file} restored")
                    st.rerun()
                except Exception as e:
                    st.error(f"Restore failed: {e}")

        with col2:
            if st.button(f"Delete backup", key=f"delete_{selected}"):
                try:
                    os.remove(selected)
                    st.warning("Backup deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")


# ===============================
# MAIN DASHBOARD
# ===============================
def run_health_dashboard():

    st.title("🧠 Smart System Health Dashboard")

    score = 0
    total_checks = 0

    files = ["users.json", "qa_dataset.csv", "pending_qa.csv", "deleted_qa.csv"]

    # ================= SYSTEM FILES =================
    st.subheader("🧾 System Files")

    for file in files:
        col1, col2, col3 = st.columns([3, 1, 1])

        status, msg = check_file(file)

        with col1:
            score += status_display(status, msg)

        with col2:
            if status == "bad":
                if st.button(f"Fix {file}", key=f"fix_{file}"):
                    create_file(file)
                    st.success(f"{file} created")
                    st.rerun()

        with col3:
            if st.button(f"Undo {file}", key=f"undo_{file}"):
                success, message = restore_last_backup(file)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        total_checks += 1

    # ================= CSV SYSTEMS =================
    for file, label in [
        ("qa_dataset.csv", "📊 Dataset"),
        ("pending_qa.csv", "⏳ Pending Q&A"),
        ("deleted_qa.csv", "🗑️ Trash System"),
    ]:
        st.subheader(label)

        status, msg = check_csv(file)
        score += status_display(status, msg)
        total_checks += 1

        col1, col2 = st.columns(2)

        with col1:
            if status != "good":
                if st.button(f"Fix {file}", key=f"fixcsv_{file}"):
                    fix_csv(file)
                    st.success(f"{file} fixed")
                    st.rerun()

        with col2:
            if st.button(f"Undo {file}", key=f"undocsv_{file}"):
                success, message = restore_last_backup(file)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    # ================= LOGS =================
    st.subheader("🚨 Error Logs")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reset Logs"):
            reset_logs()
            st.success("Logs cleared")
            st.rerun()

    with col2:
        if st.button("Undo Logs"):
            success, message = restore_last_backup("error_logs.json")
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    # ================= SCORE =================
    st.divider()

    if total_checks > 0:
        percentage = round((score / total_checks) * 100)

        if percentage >= 80:
            st.success(f"🟢 System Health: {percentage}% (Excellent)")
        elif percentage >= 50:
            st.warning(f"🟡 System Health: {percentage}% (Moderate)")
        else:
            st.error(f"🔴 System Health: {percentage}% (Critical)")

    # ================= BACKUP MANAGER =================
    st.divider()
    backup_manager_ui()