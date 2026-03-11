import streamlit as st
import requests
import sqlite3
import os

# ---------------- 1. DATABASE (Safe & Cached) ----------------
@st.cache_resource
def get_db():
    conn = sqlite3.connect("vibrant_final_v11.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, token TEXT, uid TEXT)")
    conn.commit()
    return conn

conn = get_db()
c = conn.cursor()

# ---------------- 2. PROFESSIONAL API ENGINE (Crash-Proof) ----------------
def api_call(url, params=None, token=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "auth-key": "appxapi",
        "client-service": "Appx",
        "source": "website",
        "origin": "https://www.vibrantacademy.com",
        "referer": "https://www.vibrantacademy.com/",
        "accept-language": "en-US,en;q=0.9"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            try:
                return r.json()
            except:
                return {"error": "Invalid JSON", "raw": r.text}
        return {"error": f"Server Error {r.status_code}", "raw": r.text, "code": r.status_code}
    except Exception as e:
        return {"error": str(e)}

# ---------------- 3. GLOBAL CONFIG ----------------
API_BASE = "https://vibrantacademykotaapi.akamai.net.in/get"
st.set_page_config(page_title="Vibrant Pro Elite", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #ff4b4b; color: white; }
    .stExpander { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; }
    div[data-testid="stMetricValue"] { color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 4. SIDEBAR: AUTHENTICATION ----------------
with st.sidebar:
    st.title("🛡️ Session Injector")
    email_in = st.text_input("Mobile / Email", placeholder="Target ID")
    
    if st.button("📩 Request OTP"):
        if email_in:
            with st.spinner("Processing..."):
                res = api_call(f"{API_BASE}/sendotp", {"phone": email_in})
                if "error" not in res: st.success("OTP Sent!")
                else: st.error(res["error"])
        else: st.warning("Enter ID first")

    otp_in = st.text_input("Enter OTP", type="password")
    
    if st.button("🚀 Sync Account"):
        if email_in and otp_in:
            with st.spinner("Extracting Session..."):
                v_params = {"useremail": email_in, "otp": otp_in, "device_id": "Vibrant_Elite_V11"}
                res = api_call(f"{API_BASE}/otpverify", v_params)
                
                # --- EXTRACTION BASED ON YOUR JSON (user -> token & userid) ---
                token, uid = None, None
                if isinstance(res, dict):
                    user_data = res.get("user")
                    if isinstance(user_data, dict):
                        token = user_data.get("token")
                        uid = user_data.get("userid") # Key from your JSON

                if token:
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (email_in, token, str(uid)))
                    conn.commit()
                    st.success(f"✅ Success! Welcome {res.get('user', {}).get('name', 'User')}")
                    st.rerun()
                else:
                    st.error("❌ Token capture failed.")
                    st.json(res)
        else: st.error("Fill both fields")

# ---------------- 5. MAIN DASHBOARD ----------------
users_list = [row[0] for row in c.execute("SELECT email FROM users").fetchall()]

if not users_list:
    st.info("👋 Use sidebar to login.")
    st.stop()

selected_user = st.selectbox("🎯 Target Account", users_list)
row = c.execute("SELECT token, uid FROM users WHERE email=?", (selected_user,)).fetchone()

if row:
    active_token, active_uid = row
    st.sidebar.success(f"Active: {selected_user}")
    
    m1, m2 = st.columns(2)
    m1.metric("Sessions", len(users_list))
    m2.metric("UID", active_uid)
    st.divider()

    # ---------------- 6. CLASSROOM ENGINE (Fix for 500 Error) ----------------
    if st.button("📚 Load Courses", type="primary"):
        with st.spinner("Fetching..."):
            # Try 1: user_id format
            res = api_call(f"{API_BASE}/get_user_liked_items", {"user_id": active_uid}, token=active_token)
            
            # If 500 Error, Try 2: userid format (Legacy)
            if res.get("code") == 500:
                res = api_call(f"{API_BASE}/get_user_liked_items", {"userid": active_uid}, token=active_token)

            if "error" not in res:
                st.session_state.courses_data = res.get('data', [])
                if not st.session_state.courses_data: st.warning("Account is empty.")
            else:
                st.error(f"Server rejected request. Try re-login.")
                st.json(res)

    if "courses_data" in st.session_state:
        course_map = {c.get("course_name", "Unknown"): c.get("id") for c in st.session_state.courses_data}
        choice = st.selectbox("Choose Batch", ["Select..."] + list(course_map.keys()))
        
        if choice != "Select...":
            batch_id = course_map[choice]
            with st.spinner("Scanning..."):
                l_res = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": batch_id}, token=active_token)
                lectures = l_res.get('data', {}).get('lectures', []) or l_res.get('data', [])
                
                if lectures:
                    for lec in lectures:
                        with st.expander(f"▶️ {lec.get('title', 'Lecture')}"):
                            if st.button(f"Unlock Video: {lec['id']}", key=f"v_{lec['id']}"):
                                v_url = f"{API_BASE}/fetchVideoDetailsById?course_id={batch_id}&video_id={lec['id']}&ytflag=0&folder_wise_course=1"
                                v_res = api_call(v_url, token=active_token)
                                v_data = v_res.get('data') if isinstance(v_res.get('data'), dict) else {}
                                v_path = v_data.get('video_path')
                                if v_path: st.video(v_path)
                                else: st.error("No stream found.")
                            if lec.get('pdf_url'): st.link_button("📄 PDF Notes", lec['pdf_url'])