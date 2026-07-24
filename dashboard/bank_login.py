import streamlit as st
import time

st.set_page_config(
    page_title="Internet Banking | Central Bank of India",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Global CSS with direct Cloudinary background image URL
css = """
<style>
    /* Hide Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stAppViewContainer"] { padding: 0; }
    .block-container { padding: 0 !important; max-width: 100% !important; margin: 0; }
    
    /* Background set to Blue */
    .stApp { background-color: #0f3460; margin: 0; padding: 0; }

    /* Left Column Customization with Direct Image Background */
    div[data-testid="column"]:nth-of-type(1) {
        background: linear-gradient(rgba(15, 52, 96, 0.25), rgba(15, 52, 96, 0.55)), 
                    url('https://res.cloudinary.com/vafqdl81/image/upload/f_auto,q_auto/WhatsApp_Image_2026-07-21_at_12.13.11_AM_1_brnmpo') no-repeat center center !important;
        background-size: cover !important;
        min-height: 100vh;
        padding: 0 !important;
    }

    /* Right Column Styling */
    div[data-testid="column"]:nth-of-type(2) {
        padding: 40px !important;
        background-color: #0f3460;
    }

    /* Target Text Inputs */
    .stTextInput input {
        border-radius: 4px;
        border: 1px solid #b2c5e5;
        padding: 10px;
        background-color: #ffffff;
        color: #000000 !important;
    }
    .stTextInput input:focus {
        border-color: #1976d2 !important;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2) !important;
    }

    /* Primary Buttons */
    .stButton button {
        width: 100%;
        background-color: #316ce8 !important;
        color: white !important;
        border: none;
        border-radius: 20px;
        font-weight: 600;
        padding: 6px 0;
        box-shadow: 0 2px 6px rgba(49,108,232,0.3);
    }
    .stButton button:hover {
        background-color: #1e56cb !important;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# TOP HEADER NAVBAR
header_html = """<div style="background: #1059b8; padding: 8px 36px; display: flex; align-items: center; justify-content: space-between; width: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
<div style="display: flex; align-items: center; gap: 12px;">
<img src="https://res.cloudinary.com/vafqdl81/image/upload/f_auto,q_auto/images_2_htt6iv" alt="Bank Logo" style="height: 38px; border-radius: 4px; background: white; padding: 2px; border: 1px solid #dcdcdc; object-fit: contain;">
<img src="https://res.cloudinary.com/vafqdl81/image/upload/f_auto,q_auto/images_j0sfbn" alt="Bank Logo" style="height: 38px; border-radius: 4px; background: white; padding: 2px; border: 1px solid #dcdcdc; object-fit: contain;">
<img src="https://res.cloudinary.com/vafqdl81/image/upload/f_auto,q_auto/images_1_styrma" alt="Bank Logo" style="height: 38px; border-radius: 4px; background: white; padding: 2px; border: 1px solid #dcdcdc; object-fit: contain;">
<img src="https://res.cloudinary.com/vafqdl81/image/upload/f_auto,q_auto/channels4_profile_lnrx3s" alt="Bank Logo" style="height: 38px; border-radius: 4px; background: white; padding: 2px; border: 1px solid #dcdcdc; object-fit: contain;">
</div>
<div style="display: flex; align-items: center; gap: 18px; font-family: sans-serif;">
<a href="#" style="color: white; text-decoration: none; font-size: 12px; font-weight: 500;"></a><span style="color: rgba(255,255,255,0.4);"></span><a href="#" style="color: white; text-decoration: none; font-size: 12px; font-weight: 500;"></a><span style="color: rgba(255,255,255,0.4);">|</span><a href="#" style="color: white; text-decoration: none; font-size: 12px; font-weight: 500;">NATIONAL CYBER HACKATHON 2026 - TEAM VYUH</a><span style="color: rgba(255,255,255,0.4);">|</span><a href="#" style="color: white; text-decoration: none; font-size: 12px; font-weight: 500;"></a><span style="color: rgba(255,255,255,0.4);"|</span><div style="background: white; color: #1059b8; padding: 3px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer;">English ▾</div>
</div>
</div>"""
st.markdown(header_html, unsafe_allow_html=True)

# MAIN LAYOUT
left_col, right_col = st.columns([1.5, 1], gap="small")

with left_col:
    left_banner_html = """<div style="padding: 40px 48px; position: relative; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
    <div style="position: relative; z-index: 10;">
    <h1 style="color: white; font-size: 38px; font-weight: 800; line-height: 1.15; margin-bottom: 16px;">Welcome to<br><span style="font-size: 55px;">Project Morpholock!
    </span></h1>
    <p style="color: rgba(255,255,255,0.88); font-size: 15px; max-width: 440px; line-height: 1.6; margin-bottom: 28px;">Explore our One Stop Banking Solution – your secure, user-friendly gateway to effortless banking, anytime, anywhere, and experience the seamless journey.</p>
    <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; padding: 12px 18px; display: inline-block; backdrop-filter: blur(8px);">
    <div style="color: #ffeb3b; font-size: 12px; font-weight: bold; letter-spacing: 0.5px; margin-bottom: 2px;">🛡️ MORPHOLOCK BIOMETRIC LAYER ACTIVE</div>
    <div style="color: rgba(255,255,255,0.8); font-size: 11px;">Neuromuscular Tremor Authentication | 8–12 Hz | HMAC-SHA256 | DPDP Act 2023</div>
    </div>
    </div>
    <div style="border-top: 1px solid rgba(255,255,255,0.15); padding-top: 14px; margin-top: 50px;">
    <div style="color: white; font-size: 20px; font-weight: bold; margin-bottom: 4px;"> Notice to Evaluators: </div>
    <div style="color: rgba(255,255,255,0.75); font-size: 18px; line-height: 1.5; max-width: 520px;">This page serves as a visual gateway to showcase our dashboard integration. The login fields are non-functional and strictly meant for presentation flow <a href="" target="_blank" style="color: #ffeb3b; text-decoration: underline;"></a> <br></div>
    <div style="margin-top: 10px; display: flex; gap: 16px; align-items: center;">
    <a href="#" style="color: rgba(255,255,255,0.8); font-size: 11px; text-decoration: none;"></a><span style="color: rgba(255,255,255,0.3);"></span><a href="#" style="color: rgba(255,255,255,0.8); font-size: 11px; text-decoration: none;"></a><span style="color: rgba(255,255,255,0.3);"></span><a href="#" style="color: rgba(255,255,255,0.8); font-size: 11px; text-decoration: none;"></a>
    </div>
    </div>
    </div>"""
    st.markdown(left_banner_html, unsafe_allow_html=True)

with right_col:
    # Login Card Container
    
    
    st.markdown('<div style="font-size: 16px; font-weight: bold; color: #1059b8; text-align: center;">Login to Morpholock</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 10px; color: #888; text-align: center; margin-bottom: 20px;">VERSION: V1.3.29</div>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:12px; color:#fff; font-weight:600; margin-bottom:2px;">CIF / User ID <span style="color:#ff0000;">*</span></p>', unsafe_allow_html=True)
    user_id = st.text_input("uid", placeholder="Please type here....", key="userid", label_visibility="collapsed")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    cap_col, inp_col = st.columns([1, 1], gap="small")
    with cap_col:
        st.markdown('<p style="font-size:12px; color:#fff; font-weight:600; margin-bottom:2px;">Captcha</p>', unsafe_allow_html=True)
        st.markdown("""<div style="background: #ffffff; border: 1px solid #bbb; border-radius: 4px; padding: 8px; font-family: monospace; font-size: 18px; font-weight: bold; letter-spacing: 2px; color: #000; display: flex; align-items: center; justify-content: space-between;">
        <span>168239</span><div style="display: flex; gap: 4px; font-size: 11px; cursor: pointer;"><span>🔊</span><span>🔄</span></div>
        </div>""", unsafe_allow_html=True)

    with inp_col:
        st.markdown('<p style="font-size:12px; color:#fff; font-weight:600; margin-bottom:2px;">Enter Captcha <span style="color:#d32f2f;">*</span></p>', unsafe_allow_html=True)
        captcha = st.text_input("cap", placeholder="Please type here....", key="captcha", label_visibility="collapsed")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    t_col, b_col = st.columns([1.1, 0.9], gap="small")
    with t_col:
        st.markdown('<div style="color:#1059b8; font-size:12px; font-weight:600; padding-top:8px; cursor:pointer;">Trouble Logging In ?</div>', unsafe_allow_html=True)
    with b_col:
        login_clicked = st.button("Login", key="login_btn", use_container_width=True)

    st.markdown('<div style="text-align:center; color:#999; font-size:11px; margin:16px 0; font-weight:bold;">OR</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="border: 1.5px solid #1059b8; border-radius: 20px; padding: 7px; text-align: center; color: #1059b8; font-weight: bold; font-size: 13px; cursor: pointer; margin-bottom: 20px;">Cent eeZ Registration</div>', unsafe_allow_html=True)

    widget_html = """<div style="background: #f8fafc; border-radius: 8px; padding: 10px 14px; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
    <span style="font-size: 12px; color: #444; white-space: nowrap;">I am looking for a</span>
    <select style="flex: 1; border: 1px solid #ccd6e0; border-radius: 4px; padding: 4px 6px; font-size: 12px; color: #333; background: #ffffff;">
    <option>UPI</option><option>INTERNET BANKING</option><option>ATM</option><option>MOBILE BANKING</option>
    </select>
    <button style="background: #1059b8; color: white; border: none; border-radius: 50%; width: 26px; height: 26px; font-size: 11px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center;">Go</button>
    </div>"""
    st.markdown(widget_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Login Logic Execution
    if login_clicked:
        if not user_id:
            st.error("⚠️ Please enter your CIF / User ID")
        elif captcha != "168239":
            st.error("⚠️ Incorrect captcha. Enter: 168239")
        else:
            with st.spinner("🔄 Verifying credentials..."):
                time.sleep(1)
            st.success("✅ Verified! Launching MorphoLock...")
            time.sleep(1)
            
            redirect_html = """<meta http-equiv="refresh" content="1; url='http://localhost:8502'" /><div style="text-align:center; background:white; border-radius:8px; padding:16px; margin-top:12px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <div style="font-size:32px;">🛡️</div><div style="font-size:14px; color:#1059b8; font-weight:bold; margin-top:6px;">Redirecting to MorphoLock verification...</div>
            <div style="font-size:11px; color:#777; margin-top:4px;">Please hold your sensor device</div></div>"""
            st.markdown(redirect_html, unsafe_allow_html=True)