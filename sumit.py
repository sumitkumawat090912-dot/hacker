import streamlit as st
import requests
import sqlite3
from streamlit_javascript import st_javascript

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('vibrant_final_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS portal_users 
                 (email TEXT PRIMARY KEY, token TEXT, uid TEXT, user_agent TEXT, device_id TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- BROWSER IDENTITY CAPTURE ---
# Ye script user ke browser se uska asli User-Agent uthayegi
user_agent = st_javascript("""window.navigator.userAgent""")

st.set_page_config(page_title="Vibrant Anti-Block Pro", layout="wide")

if not user_agent:
    st.info("🔄 System fingerprint verify ho raha hai... Kripya 2 second rukein.")
    st.stop()

# --- MASTER API CALLER ---
def make_vibrant_request(url, token=None, custom_ua=None):
    # Agar database mein purana UA hai to wahi bhejenge (Spoofing)
    headers = {
        "User-Agent": custom_ua if custom_ua else user_agent,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://vibrantlive.vibrantacademy.com",
        "Referer": "https://vibrantlive.vibrantacademy.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Status {response.status_code}", "raw": response.text}
    except Exception as e:
        return {"error": str(e)}

# --- UI DESIGN ---
st.title("🛡️ Vibrant Premium Dashboard (Anti-403)")

# Sidebar for Login & Accounts
with st.sidebar:
    st.header("👤 User Accounts")
    
    with st.expander("➕ Login New User"):
        email_in = st.text_input("Email/Phone")
        if st.button("Get OTP"):
            res = make_vibrant_request(f"https://vibrantacademykotaapi.akamai.net.in/get/sendotp?phone={email_in}")
            st.toast("OTP Sent!" if "error" not in res else "Error sending OTP")
            
        otp_in = st.text_input("Enter OTP", type="password")
        if st.button("Verify & Secure Save"):
            # Yahan hum device_id fix kar rahe hain taaki login stable rahe
            d_id = f"VIBRANT_WEB_{email_in[:5]}"
            v_url = f"https://vibrantacademykotaapi.akamai.net.in/get/otpverify?useremail={email_in}&otp={otp_in}&device_id={d_id}"
            res = make_vibrant_request(v_url)
            
            token = res.get('token') or res.get('data', {}).get('token')
            uid = res.get('user_id') or res.get('data', {}).get('user_id')
            
            if token:
                c.execute('INSERT OR REPLACE INTO portal_users VALUES (?, ?, ?, ?, ?)', 
                          (email_in, token, str(uid), user_agent, d_id))
                conn.commit()
                st.success("Account Saved! Reloading...")
                st.rerun()
            else:
                st.error("Login Failed. Check OTP.")

    # Account Selector
    saved_emails = [row[0] for row in c.execute('SELECT email FROM portal_users').fetchall()]
    if saved_emails:
        selected_email = st.selectbox("Switch Active Account:", saved_emails)
        c.execute('SELECT token, uid, user_agent, device_id FROM portal_users WHERE email=?', (selected_email,))
        active_token, active_uid, active_ua, active_did = c.fetchone()
    else:
        active_token = None

# --- MAIN DASHBOARD LOGIC ---
if active_token:
    st.subheader(f"Welcome, {selected_email}")
    
    # 1. Fetch Batches with SPOOFED User-Agent
    b_url = f"https://vibrantacademykotaapi.akamai.net.in/get/get_user_liked_items?user_id={active_uid}"
    batch_data = make_vibrant_request(b_url, token=active_token, custom_ua=active_ua)
    
    if batch_data and "data" in batch_data:
        batches = batch_data['data']
        batch_names = [b['course_name'] for b in batches]
        course_choice = st.selectbox("Chunye Apna Batch:", batch_names)
        
        selected_b_id = next(b['id'] for b in batches if b['course_name'] == course_choice)
        
        # 2. Fetch Content
        l_url = f"https://vibrantacademykotaapi.akamai.net.in/get/get_batch_contents?batch_id={selected_b_id}"
        lec_data = make_vibrant_request(l_url, token=active_token, custom_ua=active_ua)
        
        lectures = lec_data.get('data', {}).get('lectures') or lec_data.get('data', [])
        
        st.divider()
        for lec in lectures:
            with st.expander(f"📖 {lec['title']}"):
                col1, col2 = st.columns([3, 1])
                
                # Fetch Real Video Link dynamically
                v_id = lec['id']
                v_detail_url = f"https://vibrantacademykotaapi.akamai.net.in/get/fetchVideoDetailsById?course_id={selected_b_id}&video_id={v_id}&ytflag=0&folder_wise_course=1"
                v_res = make_vibrant_request(v_detail_url, token=active_token, custom_ua=active_ua)
                
                v_link = v_res.get('data', {}).get('video_path') if v_res else None
                
                with col1:
                    if v_link:
                        st.video(v_link)
                    else:
                        st.error("Video block hai ya link nahi mila.")
                
                with col2:
                    st.write("Resources:")
                    if lec.get('pdf_url'):
                        st.link_button("📄 Open PDF", lec['pdf_url'])
                    st.caption(f"ID: {v_id}")

else:
    st.warning("👈 Sidebar se apna account login karein.")

# --- ADMIN PANEL ---
st.sidebar.divider()
if st.sidebar.checkbox("Admin Panel (Secret)"):
    pw = st.sidebar.text_input("Password", type="password")
    if pw == "admin888":
        st.write("### All Active Portal Users")
        admin_data = c.execute('SELECT email, uid, user_agent FROM portal_users').fetchall()
        import pandas as pd
        st.table(pd.DataFrame(admin_data, columns=['Email', 'UID', 'Original User-Agent']))