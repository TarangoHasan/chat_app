import streamlit as st
import sqlite3
import hashlib
import os
import time

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database Connection
def get_db_connection():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn

# Sign-up Function
def sign_up(username, name, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    
    try:
        cursor.execute("INSERT INTO users (username, name, password) VALUES (?, ?, ?)", 
                       (username, name, hashed_password))
        conn.commit()
        st.success("✅ Account created! You can now log in.")
    except sqlite3.IntegrityError:
        st.error("⚠️ Username already exists!")
    
    conn.close()

# Sign-in Function
def sign_in(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                   (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    
    return user

# Get List of Users
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = [row["username"] for row in cursor.fetchall()]
    conn.close()
    return users

# Send Message
def send_message(sender, receiver, message, attachment=None, group_name=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO messages (sender, receiver, group_name, message, attachment) VALUES (?, ?, ?, ?, ?)", 
                   (sender, receiver, group_name, message, attachment))
    conn.commit()
    conn.close()

# Get Messages
def get_messages(sender, receiver, group_name=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if group_name:
        cursor.execute("SELECT sender, message, timestamp FROM messages WHERE group_name = ? ORDER BY timestamp", (group_name,))
    else:
        cursor.execute("SELECT sender, message, timestamp, seen FROM messages WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) ORDER BY timestamp", 
                       (sender, receiver, receiver, sender))
    
    messages = cursor.fetchall()
    conn.close()
    
    return messages

# Mark Messages as Seen
def mark_messages_as_seen(sender, receiver):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET seen = 1 WHERE sender = ? AND receiver = ?", (sender, receiver))
    conn.commit()
    conn.close()

# Save File
def save_file(user, file_name, file_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (user, file_name, file_path) VALUES (?, ?, ?)", 
                   (user, file_name, file_path))
    conn.commit()
    conn.close()

# Fetch Saved Files
def fetch_files(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, file_path FROM files WHERE user = ?", (user,))
    files = cursor.fetchall()
    conn.close()
    return files

# Notifications
def send_notification(user, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notifications (user, message) VALUES (?, ?)", 
                   (user, message))
    conn.commit()
    conn.close()

def get_notifications(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, timestamp FROM notifications WHERE user = ?", (user,))
    notifications = cursor.fetchall()
    conn.close()
    return notifications

# Streamlit App UI
st.title("🔵 Chat App")

# Session state for authentication
if "username" not in st.session_state:
    st.session_state["username"] = None

# Authentication System
if st.session_state["username"]:
    st.sidebar.write(f"✅ Logged in as: **{st.session_state['username']}**")

    if st.sidebar.button("🔴 Log Out"):
        st.session_state["username"] = None
        st.rerun()
else:
    option = st.sidebar.radio("🔐 Login / Sign Up", ["Login", "Sign Up"])
    
    if option == "Sign Up":
        new_username = st.text_input("🆔 Username")
        new_name = st.text_input("📛 Full Name")
        new_password = st.text_input("🔑 Password", type="password")
        if st.button("📝 Create Account"):
            sign_up(new_username, new_name, new_password)
    
    elif option == "Login":
        username = st.text_input("🆔 Username")
        password = st.text_input("🔑 Password", type="password")
        if st.button("🔓 Login"):
            user = sign_in(username, password)
            if user:
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

# Chat UI
if st.session_state["username"]:
    st.subheader("💬 Chat")

    user_list = get_users()
    selected_user = st.selectbox("📜 Select a User to Chat", user_list)

    if selected_user and selected_user != st.session_state["username"]:
        st.subheader(f"Chat with {selected_user}")
        
        chat_container = st.empty()
        chat_input = st.text_input("📝 Type your message...")
        
        if st.button("📤 Send"):
            if chat_input.strip():
                send_message(st.session_state["username"], selected_user, chat_input)
                chat_input = ""  # Clear input field
            else:
                st.warning("⚠️ Cannot send an empty message!")

        # Auto-refresh every 5 seconds
        while True:
            messages = get_messages(st.session_state["username"], selected_user)
            with chat_container.container():
                st.write("---")
                for msg in messages:
                    seen_status = "✔✔ Seen" if msg["seen"] else "✔ Delivered"
                    st.write(f"**{msg['sender']}**: {msg['message']} ({seen_status})")
                st.write("---")
            time.sleep(5)  # Refresh every 5 seconds

    # Settings UI
    if st.sidebar.button("⚙️ Settings"):
        st.subheader("🔧 Settings")

        current_password = st.text_input("🔑 Enter Current Password", type="password")

        if st.button("🔄 Change Username"):
            new_username = st.text_input("🆔 New Username")
            if st.button("Update Username"):
                # Check current password
                user = sign_in(st.session_state["username"], current_password)
                if user:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, st.session_state["username"]))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Username changed to {new_username}")
                    st.session_state["username"] = new_username
                    st.rerun()

        if st.button("🔄 Change Name"):
            new_name = st.text_input("📛 New Name")
            if st.button("Update Name"):
                # Check current password
                user = sign_in(st.session_state["username"], current_password)
                if user:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET name = ? WHERE username = ?", (new_name, st.session_state["username"]))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Name changed to {new_name}")
                    st.rerun()

        if st.button("🔄 Change Password"):
            new_password = st.text_input("🔑 New Password", type="password")
            if st.button("Update Password"):
                # Check current password
                user = sign_in(st.session_state["username"], current_password)
                if user:
                    hashed_new_password = hash_password(new_password)
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_new_password, st.session_state["username"]))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Password updated successfully")
                    st.rerun()

    # File Upload & Download
    uploaded_file = st.file_uploader("📤 Upload File", type=['exe', 'apk', 'py', 'mp4', 'txt', 'pdf'])
    if uploaded_file:
        save_path = f"uploads/{uploaded_file.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        save_file(st.session_state["username"], uploaded_file.name, save_path)
        st.success(f"File {uploaded_file.name} uploaded successfully!")

    # View Saved Files
    st.subheader("📂 View Saved Files")
    files = fetch_files(st.session_state["username"])
    for file in files:
        st.download_button(f"📥 Download {file['file_name']}", file['file_path'])
