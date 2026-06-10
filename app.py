import streamlit as st
import json
import datetime
import os
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ---
DATA_FILE = "chores.json"

# --- FUNCTIONS ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def get_dirtiness_status(days_passed, frequency):
    ratio = days_passed / frequency
    if ratio >= 1.0:
        return "🔴 Overdue", 1.0, "#ff4b4b"
    elif ratio >= 0.5:
        return "🟡 Getting Dirty", ratio, "#ffa421"
    else:
        return "🟢 Clean", ratio, "#21c354"

def mark_as_done(task_id, user_name):
    chores = load_data()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    for chore in chores:
        if chore["id"] == task_id:
            chore["last_done_by"] = user_name
            chore["last_date"] = today_str
            break
    save_data(chores)
    st.rerun()

def add_new_task(task_name, frequency, points, user_name):
    chores = load_data()
    new_id = max([c["id"] for c in chores], default=0) + 1
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    new_chore = {
        "id": new_id,
        "task_name": task_name,
        "frequency_days": frequency,
        "points": points,
        "last_done_by": user_name,
        "last_date": today_str
    }
    chores.append(new_chore)
    save_data(chores)
    st.rerun()

def send_overdue_emails(chores, sender_email, app_password, recipient_email):
    today = datetime.date.today()
    overdue_tasks = []
    
    for chore in chores:
        last_date = datetime.datetime.strptime(chore["last_date"], "%Y-%m-%d").date()
        days_passed = (today - last_date).days
        if days_passed >= chore["frequency_days"]:
            # Aquí estaba el error. Ahora está limpio y correcto:
            overdue_tasks.append(
                f"🚨 *{chore['task_name']}*\n"
                f"   - Days overdue: {days_passed - chore['frequency_days']}\n"
                f"   - Last done by: {chore['last_done_by']}\n"
                f"   - Last date: {chore['last_date']}"
            )

    if not overdue_tasks:
        return "✅ No overdue tasks to report! Everything is clean."

    msg = EmailMessage()
    msg['Subject'] = "🚨 Overdue Chores Alert at Home!"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    email_body = "Hello!\n\nThe following chores are overdue and need attention:\n\n" + "\n\n".join(overdue_tasks) + "\n\nPlease check the app to update the status.\n\nBest,\nYour Home Tody App 🏠"
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return "✅ Reminder email sent successfully!"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

# --- APP UI ---
st.set_page_config(page_title="Our Home Tody", page_icon="🏠", layout="wide")

st.title("🏠 Our Home Tody")
st.write("Keep track of our chores, earn points, and keep the house clean!")

# Sidebar for User and Email Settings
with st.sidebar:
    st.header("⚙️ Settings")
    current_user = st.selectbox("Who are you?", ["Tomas", "Pareja", "Guest"])
    
    st.divider()
    st.subheader("📧 Email Notifications")
    sender_email = st.text_input("Your Gmail", type="password")
    app_password = st.text_input("Gmail App Password", type="password")
    recipient_email = st.text_input("Send reminders to (Partner's email)")
    
    if st.button("📧 Check & Send Overdue Reminders"):
        if sender_email and app_password and recipient_email:
            with st.spinner("Sending emails..."):
                result = send_overdue_emails(load_data(), sender_email, app_password, recipient_email)
                st.success(result)
        else:
            st.warning("Please fill in all email fields in the sidebar.")

# 1. GAMIFICATION: Leaderboard
st.subheader("🏆 Weekly Leaderboard")
chores = load_data()
scores = {}
for chore in chores:
    user = chore["last_done_by"]
    scores[user] = scores.get(user, 0) + chore.get("points", 0)

if scores:
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    cols = st.columns(len(sorted_scores))
    for i, (user, score) in enumerate(sorted_scores):
        with cols[i]:
            st.metric(label=user, value=f"{score} pts", delta="Champion! 🏆" if i == 0 else "")
else:
    st.info("No tasks completed yet. Start cleaning to earn points!")

st.divider()

# 2. ADD NEW TASK FORM
with st.expander("➕ Add a New Chore"):
    with st.form("new_task_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_task_name = st.text_input("Task Name (e.g., Wash windows)")
        with col2:
            new_freq = st.number_input("Frequency (days)", min_value=1, value=7)
        with col3:
            new_points = st.number_input("Points reward", min_value=1, value=5)
            
        submitted = st.form_submit_button("Add Task")
        if submitted and new_task_name:
            add_new_task(new_task_name, new_freq, new_points, current_user)
            st.success(f"Added '{new_task_name}' successfully!")

st.divider()

# 3. CHORES LIST
today = datetime.date.today()

for chore in chores:
    last_date = datetime.datetime.strptime(chore["last_date"], "%Y-%m-%d").date()
    days_passed = (today - last_date).days
    
    status_text, progress_ratio, color = get_dirtiness_status(days_passed, chore["frequency_days"])
    
    with st.container(border=True):
        col_task, col_action = st.columns([3, 1])
        
        with col_task:
            st.markdown(f"### {chore['task_name']}  *(+{chore.get('points', 0)} pts)*")
            st.progress(min(progress_ratio, 1.0), text=f"Status: {status_text} | Every {chore['frequency_days']} days")
            st.caption(f"👤 Last done by: **{chore['last_done_by']}** | 📅 {days_passed} days ago ({chore['last_date']})")
            
        with col_action:
            st.write("") 
            st.write("") 
            if st.button("✅ Mark as Done", key=f"btn_{chore['id']}", type="primary"):
                mark_as_done(chore["id"], current_user)
                st.success(f"Great job, {current_user}! +{chore.get('points', 0)} points.")