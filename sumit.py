import streamlit as st
import requests
import sqlite3
import os

# ---------------- 1. DATABASE (Cached Connection) ----------------
@st.cache_resource
def get_db():
    conn = sqlite3.connect("vibrant_final_elite.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, token TEXT, uid TEXT)")
    conn.commit()
    return conn

conn = get_db()
c = conn.cursor()

# ---------------- 2. GLOBAL CONFIG & SECRET HEADERS ----------------
API_BASE = "https://vibrantacademykotaapi.akamai.net.in/get"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Aapke detected headers yahan inject kar diye hain
SECRET_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "auth-key": "appxapi",
    "client-service": "Appx",
    "source": "website",
    "origin": "https://www.vibrantacademy.com",
    "referer": "https://www.vibrantacademy.com/",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "accept-language": "en-US,en;q=0.9"
}

st.set_page_config(page_title="Vibrant Elite Bypass", layout="wide", page_icon="⚡")

# ---------------- 3. CRASH-PROOF API ENGINE ----------------
def api_call(url, params=None, token=None):
    headers = SECRET_HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        # Token ke case mein Authorization header add ho jayega
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            return {"error": f"Server Error: {r.status_code}", "raw": r.text}
        try:
            return r.json()
        except:
            return {"error": "Invalid JSON response", "raw": r.text}
    except Exception as e:
        return {"error": str(e)}

# ---------------- 4. SIDEBAR: AUTHENTICATION ----------------
with st.sidebar:
    st.title("🔑 Session Injector")
    email = st.text_input("Mobile / Email", placeholder="Target ID")
    
    if st.button("📩 Send OTP"):
        if not email:
            st.warning("Input required!")
        else:
            with st.spinner("Bypassing security..."):
                res = api_call(f"{API_BASE}/sendotp", {"phone": email})
                if "error" not in res:
                    st.success("OTP Sent!")
                    st.json(res) # Debugging ke liye response dikhana zaroori hai
                else:
                    st.error(res["error"])

    otp = st.text_input("Enter OTP", type="password", placeholder="****")
    
    if st.button("🚀 Sync Session"):
        if email and otp:
            with st.spinner("Verifying via Appx-Bypass..."):
                v_params = {"useremail": email, "otp": otp, "device_id": "Vibrant_Elite_Web"}
                res = api_call(f"{API_BASE}/otpverify", v_params)
                
                token = res.get("token") or res.get("data", {}).get("token")
                uid = res.get("user_id") or res.get("data", {}).get("user_id")

                if token:
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (email, token, str(uid)))
                    conn.commit()
                    st.success("Hijack Successful!")
                    st.rerun()
                else:
                    st.error("Bypass failed. Check logs.")
                    st.write(res)

# ---------------- 5. MAIN DASHBOARD ----------------
users_list = [row[0] for row in c.execute("SELECT email FROM users").fetchall()]

if not users_list:
    st.info("👋 Welcome! Use the Sidebar to start.")
    st.stop()

selected_user = st.selectbox("🎯 Target Account", users_list)
row = c.execute("SELECT token, uid FROM users WHERE email=?", (selected_user,)).fetchone()

if not row:
    st.error("Session missing.")
    st.stop()

active_token, active_uid = row

# UI Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Accounts", len(users_list))
c2.metric("Active UID", active_uid)
c3.metric("Bypass", "Verified")

st.divider()

# ---------------- 6. CLASSROOM CONTENT ----------------
if st.button("📚 Load Courses", type="primary"):
    with st.spinner("Fetching batches..."):
        res = api_call(f"{API_BASE}/get_user_liked_items", {"user_id": active_uid}, token=active_token)
        if "error" not in res:
            st.session_state.courses_data = res.get('data', [])
        else:
            st.error(res["error"])
            st.write(res)

if "courses_data" in st.session_state:
    course_names = {c.get("course_name", "Unknown"): c.get("id", "N/A") for c in st.session_state.courses_data}
    choice = st.selectbox("Select Batch", ["Choose..."] + list(course_names.keys()))
    
    if choice != "Choose...":
        batch_id = course_names[choice]
        with st.spinner("Scanning Lectures..."):
            l_res = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": batch_id}, token=active_token)
            lectures = l_res.get('data', {}).get('lectures', []) or l_res.get('data', [])
            
            if lectures:
                for lec in lectures:
                    with st.expander(f"🎬 {lec.get('title', 'Lecture')}"):
                        if st.button(f"Unlock Video: {lec['id']}", key=f"btn_{lec['id']}"):
                            v_url = f"{API_BASE}/fetchVideoDetailsById?course_id={batch_id}&video_id={lec['id']}&ytflag=0&folder_wise_course=1"
                            v_data = api_call(v_url, token=active_token)
                            v_path = v_data.get('data', {}).get('video_path')
                            if v_path:
                                st.video(v_path)
                            else:
                                st.error("Video path not available.")
                        
                        if lec.get('pdf_url'):
                            st.link_button("📄 Notes", lec['pdf_url'])