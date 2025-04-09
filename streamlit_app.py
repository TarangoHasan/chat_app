# streamlit_app.py
import streamlit as st
from supabase import create_client, Client
import hashlib
import os
import time
from datetime import datetime

# Supabase Configuration
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to hash passwords (can be removed if using Supabase Auth fully)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Sign-up Function
def sign_up(username, name, password):
    res = supabase.auth.sign_up({"email": username, "password": password, "data": {"full_name": name}})
    if res.error:
        st.error(f"⚠️ Sign up failed: {res.error.message}")
    else:
        st.success("✅ Account created! You can now log in.")

# Sign-in Function
def sign_in(username, password):
    res = supabase.auth.sign_in_with_password({"email": username, "password": password})
    if res.error:
        st.error("❌ Invalid username or password")
        return None
    else:
        return res.data.user

# Get List of Users
def get_users():
    response = supabase.from_("users").select("username").execute()
    if response.error:
        st.error(f"Error fetching users: {response.error.message}")
        return []
    else:
        return [row["username"] for row in response.data]

# Send Message
def send_message(sender, receiver, message, attachment=None, group_name=None):
    message_data = {"sender": sender, "receiver": receiver, "group_name": group_name, "message": message, "attachment": attachment}
    response = supabase.from_("messages").insert(message_data).execute()
    if response.error:
        st.error(f"Error sending message: {response.error.message}")

# Get Messages
def get_messages(sender, receiver, group_name=None):
    if group_name:
        response = supabase.from_("messages").select("sender, message, created_at").eq("group_name", group_name).order("created_at").execute()
    else:
        response = supabase.from_("messages").select("sender, message, created_at, seen").or_(f"and(sender.eq.{sender}, receiver.eq.{receiver}),and(sender.eq.{receiver}, receiver.eq.{sender})").order("created_at").execute()
    if response.error:
        st.error(f"Error fetching messages: {response.error.message}")
        return []
    else:
        return response.data

# Mark Messages as Seen
def mark_messages_as_seen(sender, receiver):
    response = supabase.from_("messages").update({"seen": True}).eq("sender", sender).eq("receiver", receiver).execute()
    if response.error:
        st.error(f"Error marking messages as seen: {response.error.message}")

# Save File to Supabase Storage
def save_file_to_supabase(user_id, file):
    try:
        file_name = file.name
        bucket_name = "your-storage-bucket-name"  # Replace with your bucket name
        file_path = f"{user_id}/{file_name}"
        response = supabase.storage.from_(bucket_name).upload(file_path, file.getvalue())
        if response.error:
            st.error(f"Error uploading file to Supabase Storage: {response.error.message}")
            return None
        else:
            file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
            # Optionally store the file URL in your database
            supabase.from_("files").insert({"user_id": user_id, "file_name": file_name, "file_path": file_url}).execute()
            return file_url
    except Exception as e:
        st.error(f"Error saving file to Supabase Storage: {e}")
        return None

# Fetch Saved Files (Adjust based on how you store file info)
def fetch_files(user_id):
    response = supabase.from_("files").select("file_name, file_path").eq("user_id", user_id).execute()
    if response.error:
        st.error(f"Error fetching files: {response.error.message}")
        return []
    else:
        return response.data

# Notifications
def send_notification(user, message):
    response = supabase.from_("notifications").insert({"user_id": user, "message": message}).execute()
    if response.error:
        st.error(f"Error sending notification: {response.error.message}")

def get_notifications(user):
    response = supabase.from_("notifications").select("message, created_at").eq("user_id", user).order("created_at", desc=True).execute()
    if response.error:
        st.error(f"Error fetching notifications: {response.error.message}")
        return []
    else:
        return response.data

# Streamlit App UI
st.title("🔵 Chat App")

# Session state for authentication
if "user" not in st.session_state:
    st.session_state["user"] = None

# Authentication System
if st.session_state["user"]:
    st.sidebar.write(f"✅ Logged in as: **{st.session_state['user'].email}**")

    if st.sidebar.button("🔴 Log Out"):
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.rerun()
else:
    option = st.sidebar.radio("🔐 Login / Sign Up", ["Login", "Sign Up"])

    if option == "Sign Up":
        new_username = st.text_input("🆔 Username (Email)")
        new_name = st.text_input("📛 Full Name")
        new_password = st.text_input("🔑 Password", type="password")
        if st.button("📝 Create Account"):
            sign_up(new_username, new_name, new_password)

    elif option == "Login":
        username = st.text_input("🆔 Username (Email)")
        password = st.text_input("🔑 Password", type="password")
        if st.button("🔓 Login"):
            user = sign_in(username, password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

# Chat UI
if st.session_state["user"]:
    st.subheader("💬 Chat")

    user_list = get_users()
    logged_in_username = st.session_state["user"].email
    if logged_in_username in user_list:
        user_list.remove(logged_in_username) # Don't show logged-in user in the list

    selected_user = st.selectbox("📜 Select a User to Chat", [""] + user_list) # Added an empty option

    if selected_user:
        st.subheader(f"Chat with {selected_user}")

        chat_container = st.empty()
        chat_input = st.text_input("📝 Type your message...")

        if st.button("📤 Send"):
            if chat_input.strip():
                send_message(logged_in_username, selected_user, chat_input)
                chat_input = ""  # Clear input field
            else:
                st.warning("⚠️ Cannot send an empty message!")

        # Auto-refresh every 5 seconds
        while True:
            messages = get_messages(logged_in_username, selected_user)
            with chat_container.container():
                st.write("---")
                for msg in messages:
                    seen_status = "✔✔ Seen" if msg.get("seen") else "✔ Delivered"
                    st.write(f"**{msg['sender']}**: {msg['message']} ({seen_status}) ({msg['created_at']})")
                st.write("---")
            time.sleep(5)  # Refresh every 5 seconds

    # Settings UI
    if st.sidebar.button("⚙️ Settings"):
        st.subheader("🔧 Settings")
        st.write("User settings can be managed through the Supabase Auth dashboard.")

    # File Upload & Download
    uploaded_file = st.file_uploader("📤 Upload File", type=['exe', 'apk', 'py', 'mp4', 'txt', 'pdf'])
    if uploaded_file:
        if st.session_state["user"] and st.session_state["user"].id:
            file_url = save_file_to_supabase(st.session_state["user"].id, uploaded_file)
            if file_url:
                st.success(f"File {uploaded_file.name} uploaded successfully! URL: {file_url}")
        else:
            st.warning("User ID not found. Please log in.")

    # View Saved Files
    st.subheader("📂 View Saved Files")
    if st.session_state["user"] and st.session_state["user"].id:
        files = fetch_files(st.session_state["user"].id)
        for file in files:
            st.write(f"📄 {file['file_name']}")
            st.write(f"🔗 Link: {file['file_path']}") # Display the link, you might want to create a download button with the URL
    else:
        st.info("Please log in to view saved files.")
