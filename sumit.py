import streamlit as st
import requests
import sqlite3
import os

# ---------------- 1. DATABASE ENGINE (Safe & Thread-Safe) ----------------
@st.cache_resource
def get_db():
    conn = sqlite3.connect("vibrant_final_v8.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, token TEXT, uid TEXT)")
    conn.commit()
    return conn

conn = get_db()
c = conn.cursor()

# ---------------- 2. PROFESSIONAL API ENGINE (Crash-Proof) ----------------
def api_call(url, params=None, token=None):
    # Secret Headers detected from your network logs
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
        if r.status_code != 200:
            return {"error": f"Server Error {r.status_code}", "raw": r.text}
        
        # Safe JSON Parsing
        try:
            return r.json()
        except:
            return {"error": "Invalid JSON response", "raw": r.text}
            
    except requests.exceptions.Timeout:
        return {"error": "Request Timed Out (Server Slow)"}
    except Exception as e:
        return {"error": str(e)}

# ---------------- 3. GLOBAL CONFIG ----------------
API_BASE = "https://vibrantacademykotaapi.akamai.net.in/get"
st.set_page_config(page_title="Vibrant Elite Portal", layout="wide", page_icon="🎓")

# Custom UI Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #ff4b4b; color: white; }
    .stExpander { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; }
    div[data-testid="stMetricValue"] { color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 4. SIDEBAR: AUTHENTICATION ----------------
with st.sidebar:
    st.title("🛡️ Session Hijacker")
    email_in = st.text_input("Mobile / Email", placeholder="Registered ID")
    
    if st.button("📩 Request OTP"):
        if not email_in:
            st.warning("⚠️ Input required!")
        else:
            with st.spinner("Bypassing Akamai..."):
                res = api_call(f"{API_BASE}/sendotp", {"phone": email_in})
                if "error" not in res:
                    st.success("OTP Sent! Check your device.")
                else:
                    st.error(res["error"])

    otp_in = st.text_input("Enter 4-Digit OTP", type="password", placeholder="****")
    
    if st.button("🚀 Sync Account"):
        if email_in and otp_in:
            with st.spinner("Verifying Session..."):
                v_params = {"useremail": email_in, "otp": otp_in, "device_id": "Vibrant_Elite_V8"}
                res = api_call(f"{API_BASE}/otpverify", v_params)
                
                # --- SAFE EXTRACTION (Fixed AttributeError) ---
                token, uid = None, None
                
                if isinstance(res, dict):
                    token = res.get("token")
                    uid = res.get("user_id")
                    
                    # Nested Data Check
                    data_obj = res.get("data")
                    if not token and isinstance(data_obj, dict):
                        token = data_obj.get("token")
                        uid = data_obj.get("user_id")

                if token:
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (email_in, token, str(uid)))
                    conn.commit()
                    st.success("Hijack Successful!")
                    st.rerun()
                else:
                    st.error("❌ Token not found in response.")
                    st.json(res) # Debugging help
        else:
            st.error("Fill both fields!")

# ---------------- 5. MAIN DASHBOARD ----------------
users_list = [row[0] for row in c.execute("SELECT email FROM users").fetchall()]

if not users_list:
    st.info("👋 Welcome! Use the sidebar to inject a session.")
    st.stop()

# Header Section
col_a, col_b = st.columns([2, 1])
with col_a:
    target_user = st.selectbox("🎯 Active Target", users_list)
with col_b:
    st.metric("Total Sessions", len(users_list))

# Safe Row Fetch
row = c.execute("SELECT token, uid FROM users WHERE email=?", (target_user,)).fetchone()
if not row:
    st.error("Session integrity error.")
    st.stop()

active_token, active_uid = row
st.sidebar.success(f"Logged in: {target_user}")

st.divider()

# ---------------- 6. CLASSROOM ENGINE (Optimized) ----------------
if st.button("📚 Scan My Classroom", type="primary"):
    with st.spinner("Fetching batches..."):
        res = api_call(f"{API_BASE}/get_user_liked_items", {"user_id": active_uid}, token=active_token)
        if "error" not in res:
            st.session_state.courses_data = res.get('data', [])
        else:
            st.error("Session Expired? " + res.get("error", ""))

if "courses_data" in st.session_state:
    # Safe Render
    course_map = {c.get("course_name", "Unknown"): c.get("id") for c in st.session_state.courses_data}
    choice = st.selectbox("Select Batch", ["Select..."] + list(course_map.keys()))
    
    if choice != "Select...":
        batch_id = course_map[choice]
        with st.spinner(f"Loading {choice}..."):
            l_res = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": batch_id}, token=active_token)
            lectures = l_res.get('data', {}).get('lectures', []) or l_res.get('data', [])
            
            if lectures:
                st.subheader(f"📖 Lectures for {choice}")
                for lec in lectures:
                    with st.expander(f"▶️ {lec.get('title', 'Untitled')}"):
                        # Lazy Load Video logic
                        if st.button(f"Load Video: {lec['id']}", key=f"v_{lec['id']}"):
                            v_url = f"{API_BASE}/fetchVideoDetailsById?course_id={batch_id}&video_id={lec['id']}&ytflag=0&folder_wise_course=1"
                            v_res = api_call(v_url, token=active_token)
                            v_path = v_res.get('data', {}).get('video_path')
                            if v_path:
                                st.video(v_path)
                            else:
                                st.error("Video path empty.")
                        
                        if lec.get('pdf_url'):
                            st.link_button("📄 PDF Notes", lec['pdf_url'])
            else:
                st.info("Batch is empty.")

# ---------------- 7. ADMIN TERMINAL ----------------
st.sidebar.divider()
if st.sidebar.checkbox("🔧 Dev Tools"):
    if st.sidebar.text_input("Root Pass", type="password") == "admin888":
        st.write("### Database Session Dump")
        st.dataframe(c.execute("SELECT * FROM users").fetchall(), use_container_width=True)
        if st.button("🗑️ Wipe Sessions"):
            c.execute("DELETE FROM users")
            conn.commit()
            st.rerun()