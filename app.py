import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Load environment variables ----------
load_dotenv()

st.set_page_config(page_title="SuperBrain AI", layout="wide")
st.image("/mnt/data/Super Brain.png", width=160)
api_key = os.getenv("OPENAI_API_KEY", "")

# ---------- Error if no API key ----------
if not api_key:
    st.error(
        "❌ No OpenAI API key found.\n\n"
        "Set **OPENAI_API_KEY** in your `.env` file (local) or Streamlit Cloud Secrets."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ---------- Billing / plan settings ----------
APP_NAME = "SuperBrain AI"

FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 5))  
PREMIUM_ACCESS_CODE = os.getenv("PREMIUM_ACCESS_CODE", "")

# ---------- Session state ----------
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "premium_activated_at" not in st.session_state:
    st.session_state.premium_activated_at = None

# ============================
# 🔹 LOGO + PREMIUM BANNER
# ============================
st.markdown(
    """
    <style>
        .centered-img {
            display: flex;
            justify-content: center;
            margin-bottom: -10px;
        }

        .premium-badge {
            text-align: center;
            background: linear-gradient(90deg, #4f46e5, #9333ea);
            color: white;
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 14px;
            display: inline-block;
            margin-bottom: 20px;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ⭐ Logo
st.markdown(
    f"""
    <div class="centered-img">
        <img src="/mnt/data/Super Brain.png" width="160">
    </div>
    """,
    unsafe_allow_html=True,
)

# ⭐ Premium Banner
if st.session_state.is_premium:
    st.markdown(
        '<div class="premium-badge">✨ Premium User — Unlimited Access</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="premium-badge" style="background:#f59e0b;">⚡ Free User — Limited Access</div>',
        unsafe_allow_html=True,
    )


# --------------------------------
# Helper Functions
# --------------------------------
def can_use_ai():
    """Check if user still has remaining free requests."""
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"⚠️ Free limit reached ({FREE_DAILY_LIMIT} requests).\n\n"
            "Upgrade to premium for **unlimited access**."
        )
        return False
    return True


def register_request():
    """Count API usage for free users."""
    if not st.session_state.is_premium:
        st.session_state.request_count += 1


def call_openai(system_prompt, user_prompt):
    """Generic AI request handler."""
    if not can_use_ai():
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        register_request()
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error calling OpenAI API: {e}"


# ============================
# SIDEBAR UI
# ============================
st.sidebar.title(APP_NAME)

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
if theme == "Dark":
    st.markdown(
        """
        <style>
        .stApp { background-color: #0D1117; color: #E6EDF3; }
        </style>
        """,
        unsafe_allow_html=True,
    )

mode = st.sidebar.selectbox(
    "Choose AI Tool:",
    [
        "General Chat",
        "Resume & Cover Letter",
        "Blog / Social Post Writer",
        "Email Writer",
        "Code Helper",
    ],
)

st.sidebar.subheader("Usage")
remaining = (
    "Unlimited"
    if st.session_state.is_premium
    else FREE_DAILY_LIMIT - st.session_state.request_count
)
st.sidebar.write(f"Requests used: {st.session_state.request_count}")
st.sidebar.write(f"Remaining: {remaining}")

if not st.session_state.is_premium:
    st.sidebar.progress(
        st.session_state.request_count / FREE_DAILY_LIMIT
    )

# =======================
# PREMIUM UNLOCK
# =======================
st.sidebar.subheader("🔑 Have a Premium Code?")
input_code = st.sidebar.text_input("Enter Access Code", type="password")
if st.sidebar.button("Unlock Premium"):
    if input_code == PREMIUM_ACCESS_CODE:
        st.session_state.is_premium = True
        st.session_state.request_count = 0
        st.success("🎉 Premium Unlocked — Enjoy Unlimited Access!")
    else:
        st.error("❌ Invalid access code.")

st.sidebar.write("---")
st.sidebar.subheader("💳 Upgrade to Premium")
st.sidebar.markdown(
    "[Pay ₹299 on Razorpay](https://rzp.io/rzp/HuxrI9w)"
)
st.sidebar.caption("After payment, a premium code will be sent to your email.")

# ============================
# MAIN WORK AREA
# ============================

st.title(APP_NAME)
st.caption("Your multi-skill AI assistant powered by OpenAI + Streamlit.")

# ----------------------------------
# 1️⃣ GENERAL CHAT
# ----------------------------------
if mode == "General Chat":
    st.subheader("💬 Chat with AI")

    user_msg = st.text_area("Type your message:")
    if st.button("Send"):
        if user_msg.strip():
            st.session_state.chat_history.append(("You", user_msg))

            messages = [{"role": "system", "content": "You are a helpful AI."}]
            for role, msg in st.session_state.chat_history:
                messages.append({"role": "user" if role == "You" else "assistant", "content": msg})

            if can_use_ai():
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                    )
                    reply = res.choices[0].message.content
                    register_request()
                    st.session_state.chat_history.append(("AI", reply))
                except Exception as e:
                    st.error(e)

    st.write("---")
    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role}:** {msg}")

# ----------------------------------
# 2️⃣ RESUME MAKER
# ----------------------------------
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter Builder")

    name = st.text_input("Name")
    role = st.text_input("Job Role")
    skills = st.text_area("Skills")
    exp = st.text_area("Experience")
    projects = st.text_area("Projects")

    if st.button("Generate"):
        prompt = f"""
Create resume content.

Name: {name}
Role: {role}
Skills: {skills}
Experience: {exp}
Projects: {projects}
"""
        output = call_openai("You are HR expert.", prompt)
        st.write(output)

# ----------------------------------
# 3️⃣ BLOG WRITER
# ----------------------------------
elif mode == "Blog / Social Post Writer":
    st.subheader("✍️ Blog Writer")

    topic = st.text_input("Topic")
    if st.button("Generate Blog"):
        output = call_openai("You are blog writer.", f"Write blog about {topic}")
        st.write(output)

# ----------------------------------
# 4️⃣ EMAIL WRITER
# ----------------------------------
elif mode == "Email Writer":
    st.subheader("📧 Email Writer")

    purpose = st.text_input("Purpose")
    context = st.text_area("Context")
    if st.button("Generate Email"):
        output = call_openai("You are email expert.", f"Write email for: {purpose}\n{context}")
        st.write(output)

# ----------------------------------
# 5️⃣ CODE HELPER
# ----------------------------------
elif mode == "Code Helper":
    st.subheader("💻 Code Debugger")

    code_text = st.text_area("Paste your code")
    if st.button("Explain Code"):
        output = call_openai("You are senior developer.", f"Explain this code:\n{code_text}")
        st.write(output)

