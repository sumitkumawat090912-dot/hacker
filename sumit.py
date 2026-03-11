import streamlit as st
import cloudscraper
import sqlite3
import os
from cryptography.fernet import Fernet
from datetime import datetime

# --- SECURITY & ENCRYPTION ---
# Browser ki identity ko mimic karne wala scraper
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

if not os.path.exists("secret.key"):
    with open("secret.key", "wb") as f: f.write(Fernet.generate_key())
cipher = Fernet(open("secret.key", "rb").read())

# --- DATABASE CONNECTION ---
conn = sqlite3.connect('vibrant_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, token TEXT, uid TEXT, last_seen TEXT)')
conn.commit()

# --- CORE FUNCTIONS ---
def bypass_get(url, token=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://vibrantlive.vibrantacademy.com/",
        "Origin": "https://vibrantlive.vibrantacademy.com",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = scraper.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            st.error("🚨 Akamai 403: Security is tight right now. Try again in 5 mins.")
        return None
    except Exception as e:
        st.error(f"Network Error: {str(e)}")
        return None

# --- STREAMLIT UI ---
st.set_page_config(page_title="Vibrant Bypass Pro", layout="wide")

# Custom CSS for App Look
st.markdown("""
<style>
    .stVideo { border-radius: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5); }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .reportview-container { background: #0f1116; }
</style>
""", unsafe_allow_html=True)

# Navigation
st.sidebar.title("💎 Vibrant Cloud")
page = st.sidebar.radio("Go to:", ["Login/Home", "My Classroom", "Admin Control"])

# --- PAGE 1: LOGIN ---
if page == "Login/Home":
    st.title("🛡️ Secure Login")
    st.info("Akamai-Bypass mode is ACTIVE.")
    
    email = st.text_input("Email ID / Phone Number")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send OTP", use_container_width=True):
            res = bypass_get(f"https://vibrantacademykotaapi.akamai.net.in/get/sendotp?phone={email}")
            if res: st.success("OTP sent to your device!")

    with col2:
        otp = st.text_input("Enter OTP", type="password")
        if st.button("Verify & Link", use_container_width=True):
            res = bypass_get(f"https://vibrantacademykotaapi.akamai.net.in/get/otpverify?useremail={email}&otp={otp}&device_id=Chrome_Web_V3")
            if res and (res.get('token') or res.get('data')):
                token = res.get('token') or res.get('data', {}).get('token')
                uid = res.get('user_id') or res.get('data', {}).get('user_id')
                
                # Encrypt and Save to DB
                enc_token = cipher.encrypt(token.encode()).decode()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', (email, enc_token, str(uid), now))
                conn.commit()
                st.session_state.current_user = email
                st.success("✅ Account Saved! Go to 'My Classroom'")

# --- PAGE 2: CLASSROOM ---
elif page == "My Classroom":
    saved_accounts = [row[0] for row in c.execute('SELECT email FROM users').fetchall()]
    
    if not saved_accounts:
        st.warning("Pehle Login karein!")
    else:
        active_user = st.selectbox("Select Account", saved_accounts)
        c.execute('SELECT token, uid FROM users WHERE email=?', (active_user,))
        token_data, uid = c.fetchone()
        token = cipher.decrypt(token_data.encode()).decode()
        
        st.title(f"📖 Welcome, {active_user}")
        
        # 1. Batches
        batches = bypass_get(f"https://vibrantacademykotaapi.akamai.net.in/get/get_user_liked_items?user_id={uid}", token=token)
        
        if batches and batches.get('data'):
            b_list = batches['data']
            selected_b = st.selectbox("Choose Batch", [b['course_name'] for b in b_list])
            b_id = next(b['id'] for b in b_list if b['course_name'] == selected_b)
            
            # 2. Lectures
            st.divider()
            lectures = bypass_get(f"https://vibrantacademykotaapi.akamai.net.in/get/get_batch_contents?batch_id={b_id}", token=token)
            
            if lectures:
                lec_data = lectures.get('data', {}).get('lectures') or lectures.get('data', [])
                search = st.text_input("🔍 Search lecture...")
                
                for lec in lec_data:
                    if search.lower() in lec['title'].lower():
                        with st.expander(f"▶️ {lec['title']}"):
                            # Final Video Link Bypass
                            v_url = f"https://vibrantacademykotaapi.akamai.net.in/get/fetchVideoDetailsById?course_id={b_id}&video_id={lec['id']}&ytflag=0&folder_wise_course=1"
                            v_res = bypass_get(v_url, token=token)
                            
                            v_path = v_res.get('data', {}).get('video_path') if v_res else None
                            if v_path:
                                st.video(v_path)
                            st.link_button("📄 Open PDF Notes", lec.get('pdf_url', '#'), use_container_width=True)

# --- PAGE 3: ADMIN ---
elif page == "Admin Control":
    st.title("🛡️ Management Console")
    pw = st.text_input("Enter Master Password", type="password")
    if pw == "admin888":
        st.write("### Total Logged Users")
        users = c.execute('SELECT email, uid, last_seen FROM users').fetchall()
        import pandas as pd
        df = pd.DataFrame(users, columns=['Email', 'UID', 'Last Login'])
        st.table(df)
        
        if st.button("Purge Database"):
            c.execute('DELETE FROM users')
            conn.commit()
            st.rerun()
    else:
        st.error("Access Restricted.")