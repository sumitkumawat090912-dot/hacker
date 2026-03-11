import streamlit as st
import requests
import os
from cryptography.fernet import Fernet
import json
from datetime import datetime

# --- Encryption System ---
# Note: Real deployment mein 'ENCRYPTION_KEY' ko Streamlit Secrets mein rakhein
if 'enc_key' not in st.session_state:
    st.session_state.enc_key = Fernet.generate_key()
cipher = Fernet(st.session_state.enc_key)

# --- Configuration ---
BASE_URL = "https://vibrantacademykotaapi.akamai.net.in/get"
DEVICE_ID = "Universal_Vibrant_Web_v1"

# --- UI Setup ---
st.set_page_config(page_title="Vibrant Community Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stSidebar { background-color: #1a1c23; border-right: 1px solid #333; }
    .lecture-card { padding: 15px; border-radius: 10px; border: 1px solid #444; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Database / State Initialization ---
if 'db' not in st.session_state:
    st.session_state.db = {} # Public use ke liye yahan Supabase/PostgreSQL use hota hai

# --- Helper Functions ---
def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt(text):
    return cipher.decrypt(text.encode()).decode()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎛️ Navigation")
page = st.sidebar.radio("Go to:", ["Home", "My Classroom", "Admin Panel"])

# --- PAGE 1: HOME (LOGIN) ---
if page == "Home":
    st.title("🎓 Vibrant Student Login")
    st.write("Apne account se connect karke lectures unlock karein.")
    
    with st.container():
        login_col1, login_col2 = st.columns(2)
        with login_col1:
            email = st.text_input("Enter Email or Phone")
            if st.button("Send OTP"):
                requests.get(f"{BASE_URL}/sendotp?phone={email}")
                st.toast("OTP Sent successfully!")
        
        with login_col2:
            otp = st.text_input("Enter 4-Digit OTP", type="password")
            if st.button("Verify & Link Account"):
                res = requests.get(f"{BASE_URL}/otpverify?useremail={email}&otp={otp}&device_id={DEVICE_ID}").json()
                token = res.get('token') or res.get('data', {}).get('token')
                uid = res.get('user_id') or res.get('data', {}).get('user_id')
                
                if token:
                    # Encrypt and Save to Session (Admin can see count)
                    st.session_state.db[email] = {
                        "token": encrypt(token),
                        "uid": uid,
                        "last_login": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.current_user = email
                    st.success(f"Account Linked: {email}")
                else:
                    st.error("Invalid OTP or Access Denied.")

# --- PAGE 2: CLASSROOM ---
elif page == "My Classroom":
    if 'current_user' not in st.session_state:
        st.warning("⚠️ Pehle Home page par ja kar login karein.")
    else:
        user_info = st.session_state.db[st.session_state.current_user]
        headers = {"Authorization": f"Bearer {decrypt(user_info['token'])}"}
        
        st.title(f"📚 Classroom - {st.session_state.current_user}")
        
        # 1. Fetch Batches
        batch_res = requests.get(f"{BASE_URL}/get_user_liked_items?user_id={user_info['uid']}", headers=headers).json()
        batches = batch_res.get('data', [])
        
        if batches:
            selected_b_name = st.selectbox("Select Your Batch", [b['course_name'] for b in batches])
            b_id = next(b['id'] for b in batches if b['course_name'] == selected_b_name)
            
            # 2. Fetch Lectures
            st.divider()
            content_res = requests.get(f"{BASE_URL}/get_batch_contents?batch_id={b_id}", headers=headers).json()
            lectures = content_res.get('data', {}).get('lectures') or content_res.get('data', [])
            
            search = st.text_input("🔍 Search Lectures", "")
            
            for lec in lectures:
                if search.lower() in lec.get('title', '').lower():
                    with st.expander(f"🎬 {lec.get('title')}"):
                        v_id = lec.get('id')
                        # Real-time Details from Vibrant API
                        v_details = requests.get(f"{BASE_URL}/fetchVideoDetailsById?course_id={b_id}&video_id={v_id}&ytflag=0&folder_wise_course=1", headers=headers).json()
                        
                        v_path = v_details.get('data', {}).get('video_path')
                        p_path = lec.get('pdf_url')
                        
                        v_col, p_col = st.columns([3, 1])
                        with v_col:
                            if v_path:
                                st.video(v_path)
                            else:
                                st.info("Video link processing...")
                        with p_col:
                            st.write("Resources")
                            if p_path: st.link_button("📄 Open PDF", p_path)
                            st.caption(f"Lecture ID: {v_id}")
        else:
            st.error("Is account mein koi active batch nahi mila.")

# --- PAGE 3: ADMIN PANEL ---
elif page == "Admin Panel":
    st.title("🛡️ Admin Control Center")
    admin_pass = st.sidebar.text_input("Admin Password", type="password")
    
    if admin_pass == "Vibrant2026": # Isse badal dein
        st.subheader("User Statistics")
        total_logins = len(st.session_state.db)
        st.metric("Total Connected Accounts", total_logins)
        
        if total_logins > 0:
            # Create a table for admin to see who logged in
            data_list = []
            for email, info in st.session_state.db.items():
                data_list.append({
                    "Email/Phone": email,
                    "User ID": info['uid'],
                    "Last Activity": info['last_login'],
                    "Status": "Encrypted & Active"
                })
            st.table(data_list)
            
            if st.button("Clear Database"):
                st.session_state.db = {}
                st.rerun()
        else:
            st.info("Abhi tak kisi ne login nahi kiya.")
    else:
        st.error("Admin access denied. Sahi password enter karein.")