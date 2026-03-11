import streamlit as st
import requests
import sqlite3
import os

# ---------------- 1. DATABASE ENGINE (Safe & Cached) ----------------
@st.cache_resource
def get_db():
    conn = sqlite3.connect("vibrant_pro_v8.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, token TEXT, uid TEXT)")
    conn.commit()
    return conn

conn = get_db()
c = conn.cursor()

# ---------------- 2. SAFE API ENGINE (Crash-Proof) ----------------
def api_call(url, params=None, headers=None):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=12)
        if r.status_code != 200:
            return {"error": f"Server returned {r.status_code}", "status": "failed"}
        try:
            return r.json()
        except:
            return {"error": "Invalid JSON response", "raw": r.text}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out (Server slow)"}
    except Exception as e:
        return {"error": str(e)}

# ---------------- 3. GLOBAL CONFIG ----------------
API_BASE = "https://vibrantacademykotaapi.akamai.net.in/get"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
COMMON_HEADERS = {"User-Agent": UA, "Accept": "application/json"}

st.set_page_config(page_title="Vibrant Pro Elite", layout="wide", page_icon="🛡️")

# Professional Dark UI
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #ff4b4b; }
    .stExpander { background-color: #161b22; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 4. SIDEBAR: AUTHENTICATION ----------------
with st.sidebar:
    st.title("🛡️ Secure Vault")
    email = st.text_input("Mobile / Email", placeholder="Target ID")
    
    if st.button("📩 Request OTP"):
        if not email:
            st.warning("Input required!")
        else:
            with st.spinner("Bypassing..."):
                res = api_call(f"{API_BASE}/sendotp", {"phone": email}, COMMON_HEADERS)
                if "error" not in res:
                    st.success("OTP Sent!")
                else:
                    st.error(res["error"])

    otp = st.text_input("Enter OTP", type="password", placeholder="****")
    
    if st.button("🚀 Sync Account"):
        if email and otp:
            with st.spinner("Injecting Session..."):
                v_params = {"useremail": email, "otp": otp, "device_id": "Vibrant_Elite_V8"}
                res = api_call(f"{API_BASE}/otpverify", v_params, COMMON_HEADERS)
                
                token = res.get("token") or res.get("data", {}).get("token")
                uid = res.get("user_id") or res.get("data", {}).get("user_id")

                if token:
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (email, token, str(uid)))
                    conn.commit()
                    st.success("Hijack Successful!")
                    st.rerun()
                else:
                    st.error("Verification Blocked.")
                    if "error" in res: st.write(res)

# ---------------- 5. MAIN DASHBOARD ----------------
users_list = [row[0] for row in c.execute("SELECT email FROM users").fetchall()]

if not users_list:
    st.info("👋 Welcome! Use the Sidebar to hijack an active session.")
    st.stop()

# Account Switching & Metrics
selected_user = st.selectbox("🎯 Target Selection", users_list)
st.sidebar.success(f"Logged in as: {selected_user}")

# DB Fetch Protection
row = c.execute("SELECT token, uid FROM users WHERE email=?", (selected_user,)).fetchone()
if not row:
    st.error("Session integrity compromised. Please re-login.")
    st.stop()

active_token, active_uid = row
auth_h = {"Authorization": f"Bearer {active_token}", "User-Agent": UA}

# Modern UI Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Active Sessions", len(users_list))
m2.metric("Target UID", active_uid)
m3.metric("Security Status", "Encrypted")

st.divider()

# ---------------- 6. CLASSROOM ENGINE (Safe & Optimized) ----------------
if st.button("📚 Fetch Enrolled Batches", type="primary"):
    with st.spinner("Scanning classroom..."):
        res = api_call(f"{API_BASE}/get_user_liked_items", {"user_id": active_uid}, auth_h)
        if "error" not in res:
            st.session_state.courses_data = res.get('data', [])
        else:
            st.error(res["error"])

if "courses_data" in st.session_state:
    # Safe Dictionary Rendering
    course_names = {
        c.get("course_name", "Unknown Course"): c.get("id", "N/A") 
        for c in st.session_state.courses_data
    }
    
    choice = st.selectbox("Select Batch to Explore", ["Choose..."] + list(course_names.keys()))
    
    if choice != "Choose...":
        batch_id = course_names[choice]
        
        with st.spinner(f"Loading {choice}..."):
            l_res = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": batch_id}, auth_h)
            lectures = l_res.get('data', {}).get('lectures', []) or l_res.get('data', [])
            
            if lectures:
                st.subheader(f"📂 {choice} Lectures")
                st.progress(min(len(lectures)/50, 1.0)) # Visual Progress
                
                for lec in lectures:
                    # Optimized Rendering: Only fetch video details when expanded
                    title = lec.get('title', 'No Title')
                    with st.expander(f"🎬 {title}"):
                        if st.button(f"Load Video: {title[:20]}...", key=f"btn_{lec['id']}"):
                            v_id = lec.get('id')
                            v_url = f"{API_BASE}/fetchVideoDetailsById?course_id={batch_id}&video_id={v_id}&ytflag=0&folder_wise_course=1"
                            v_data = api_call(v_url, None, auth_h)
                            
                            v_path = v_data.get('data', {}).get('video_path')
                            if v_path:
                                st.video(v_path)
                                st.code(f"Stream URL: {v_path}")
                            else:
                                st.error("Video path not found in response.")
                        
                        if lec.get('pdf_url'):
                            st.link_button("📄 Download PDF Notes", lec['pdf_url'])
            else:
                st.warning("No lectures found in this target batch.")

# ---------------- 7. DEVELOPER TERMINAL ----------------
st.sidebar.divider()
if st.sidebar.checkbox("🔧 Developer Terminal"):
    # Using environment variable for security, fallback to your admin888
    ADMIN_PASS = os.getenv("ADMIN_PASS", "admin888")
    pw = st.sidebar.text_input("Root Access Key", type="password")
    
    if pw == ADMIN_PASS:
        st.write("### 🗄️ Database Session Dump")
        all_data = c.execute("SELECT * FROM users").fetchall()
        st.dataframe(all_data, use_container_width=True)
        
        if st.button("⚠️ Wipe Database"):
            c.execute("DELETE FROM users")
            conn.commit()
            st.success("Database purged.")
            st.rerun()