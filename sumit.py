import streamlit as st
import requests
import sqlite3
from streamlit_javascript import st_javascript

# --- DATABASE ENGINE ---
conn = sqlite3.connect('vibrant_final_bypass.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, token TEXT, uid TEXT, ua TEXT)')
conn.commit()

# --- CONFIG FROM YOUR LOGS ---
MOZILLA_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
VERCEL_IP = "76.76.21.21"
ORIGIN_REF = "https://www.vibrantacademy.com/"

st.set_page_config(page_title="Vibrant Bypass Pro", layout="wide")

# --- CUSTOM CSS (Hacker Dark Theme) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    .stSidebar {{ background-color: #161b22; border-right: 1px solid #30363d; }}
    div[data-testid="stExpander"] {{ border: 1px solid #30363d; background: #0d1117; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Vercel-React Stealth Engine")
st.caption(f"Status: Connected to {VERCEL_IP} | UA: Mozilla Firefox")

# --- SIDEBAR: LOGIN ---
with st.sidebar:
    st.header("🔑 Hijack Session")
    u_email = st.text_input("Mobile/Email")
    
    # JavaScript Injection for OTP (Akamai bypass)
    if st.button("GET OTP (Client-Inject)"):
        # Hum Python ke bajaye user ke browser se request fire karenge
        js_otp = f"""
        fetch("https://vibrantacademykotaapi.akamai.net.in/get/sendotp?phone={u_email}", {{
            headers: {{ 
                "User-Agent": "{MOZILLA_UA}",
                "Referer": "{ORIGIN_REF}"
            }}
        }}).then(r => console.log("OTP Hijacked"));
        """
        st_javascript(js_otp)
        st.success("Target Hit! OTP Sent via Browser Engine.")

    u_otp = st.text_input("Enter OTP", type="password")
    if st.button("VERIFY & SAVE"):
        # Verification using Spoofed Vercel Headers
        v_url = f"https://vibrantacademykotaapi.akamai.net.in/get/otpverify?useremail={u_email}&otp={u_otp}&device_id=Vercel_React_Bypass_v1"
        
        headers = {
            "User-Agent": MOZILLA_UA,
            "Origin": ORIGIN_REF.strip('/'),
            "Referer": ORIGIN_REF,
            "X-Forwarded-For": VERCEL_IP,
            "X-Real-IP": VERCEL_IP
        }
        
        try:
            res = requests.get(v_url, headers=headers).json()
            token = res.get('token') or res.get('data', {}).get('token')
            uid = res.get('user_id') or res.get('data', {}).get('user_id')
            
            if token:
                c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', (u_email, token, str(uid), MOZILLA_UA))
                conn.commit()
                st.success("Session Saved in Database!")
                st.rerun()
            else:
                st.error("Verification Blocked. Try again.")
        except:
            st.error("Connection Interrupted.")

# --- MAIN DASHBOARD ---
saved_accs = [row[0] for row in c.execute('SELECT email FROM users').fetchall()]

if saved_accs:
    target = st.selectbox("Switch Account", saved_accs)
    c.execute('SELECT token, uid FROM users WHERE email=?', (target,))
    t_token, t_uid = c.fetchone()
    
    m_headers = {
        "Authorization": f"Bearer {t_token}",
        "User-Agent": MOZILLA_UA,
        "Referer": ORIGIN_REF,
        "X-Forwarded-For": VERCEL_IP
    }
    
    # 1. Fetch Batches
    b_res = requests.get(f"https://vibrantacademykotaapi.akamai.net.in/get/get_user_liked_items?user_id={t_uid}", headers=m_headers).json()
    
    if b_res.get('data'):
        selected_b = st.selectbox("Select Batch", [b['course_name'] for b in b_res['data']])
        b_id = next(b['id'] for b in b_res['data'] if b['course_name'] == selected_b)
        
        # 2. Fetch Content
        l_res = requests.get(f"https://vibrantacademykotaapi.akamai.net.in/get/get_batch_contents?batch_id={b_id}", headers=m_headers).json()
        lectures = l_res.get('data', {}).get('lectures') or l_res.get('data', [])
        
        for lec in lectures:
            with st.expander(f"🔓 {lec['title']}"):
                # Video Detail Fetch
                v_url = f"https://vibrantacademykotaapi.akamai.net.in/get/fetchVideoDetailsById?course_id={b_id}&video_id={lec['id']}&ytflag=0&folder_wise_course=1"
                v_res = requests.get(v_url, headers=m_headers).json()
                v_path = v_res.get('data', {}).get('video_path')
                
                if v_path:
                    st.video(v_path)
                st.link_button("📄 Notes", lec.get('pdf_url', '#'))
else:
    st.info("👈 Sidebar se login hijack karein.")

# --- ADMIN TERMINAL ---
if st.sidebar.checkbox("Terminal Dashboard"):
    if st.sidebar.text_input("Root Access", type="password") == "admin888":
        st.write("### 🗄️ Database Logs")
        st.table(c.execute('SELECT email, uid FROM users').fetchall())