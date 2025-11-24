import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------
# Load environment variables
# ---------------------------------------------------
load_dotenv()

st.set_page_config(page_title="SuperBrain AI", layout="wide")

# ---------------------------------------------------
# Display Logo (must exist in repo as SuperBrain.png)
# ---------------------------------------------------
st.markdown(
    """
    <div style='text-align:center; margin-top: -20px; margin-bottom: 10px;'>
        <img src='SuperBrain.png' width='160'>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# Load OpenAI API Key
# ---------------------------------------------------
api_key = os.getenv("OPENAI_API_KEY", "")
if not api_key:
    st.error("Missing OPENAI_API_KEY. Add it in Streamlit > Settings > Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---------------------------------------------------
# Billing / Premium Settings
# ---------------------------------------------------
APP_NAME = "SuperBrain AI"
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 5))
PREMIUM_ACCESS_CODE = os.getenv("PREMIUM_ACCESS_CODE", "")

# ---------------------------------------------------
# Session State
# ---------------------------------------------------
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------
# Premium Banner
# ---------------------------------------------------
st.markdown(
    """
    <style>
    .premium-badge {
        text-align: center;
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.is_premium:
    st.markdown(
        "<div class='premium-badge' style='background:#4f46e5; color:white;'>✨ Premium User — Unlimited Access</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div class='premium-badge' style='background:#f59e0b; color:white;'>⚡ Free User — Limited Access</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def can_use_ai():
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning("⚠️ You reached the free limit. Upgrade to premium for unlimited access.")
        return False

    return True


def register_request():
    if not st.session_state.is_premium:
        st.session_state.request_count += 1


def call_openai(system_prompt, user_prompt):
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
        return f"Error: {e}"


# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
st.sidebar.title(APP_NAME)

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
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
        "Blog Writer",
        "Email Writer",
        "Code Helper",
    ],
)

st.sidebar.subheader("Usage")
remaining = (
    "Unlimited" if st.session_state.is_premium
    else FREE_DAILY_LIMIT - st.session_state.request_count
)
st.sidebar.write(f"Used: {st.session_state.request_count}")
st.sidebar.write(f"Remaining: {remaining}")

if not st.session_state.is_premium:
    st.sidebar.progress(st.session_state.request_count / FREE_DAILY_LIMIT)

# Premium unlock
st.sidebar.subheader("🔑 Have a Premium Code?")
entered = st.sidebar.text_input("Enter Code", type="password")
if st.sidebar.button("Unlock Premium"):
    if entered == PREMIUM_ACCESS_CODE:
        st.session_state.is_premium = True
        st.success("🎉 Premium Activated!")
    else:
        st.error("Invalid code.")

# Payment link
st.sidebar.write("---")
st.sidebar.subheader("💳 Upgrade to Premium")
st.sidebar.markdown("[Pay ₹299 on Razorpay](https://rzp.io/rzp/HuxrI9w)")


# ---------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------
st.title(APP_NAME)
st.caption("Your multi-skill AI assistant powered by OpenAI + Streamlit.")


# ----------------- 1️⃣ GENERAL CHAT -----------------
if mode == "General Chat":
    st.subheader("💬 Chat with AI")

    user_msg = st.text_area("Enter message:")
    if st.button("Send"):
        if user_msg.strip():
            st.session_state.chat_history.append(("You", user_msg))

            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            for role, msg in st.session_state.chat_history:
                messages.append({"role": "user" if role == "You" else "assistant", "content": msg})

            if can_use_ai():
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )
                reply = response.choices[0].message.content
                register_request()
                st.session_state.chat_history.append(("AI", reply))

    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role}:** {msg}")

# ----------------- 2️⃣ RESUME -----------------
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume Builder")

    name = st.text_input("Name")
    role = st.text_input("Target Role")
    skills = st.text_area("Skills")
    exp = st.text_area("Experience")
    projects = st.text_area("Projects")

    if st.button("Generate Resume"):
        prompt = f"""
Name: {name}
Role: {role}
Skills: {skills}
Experience: {exp}
Projects: {projects}
Create resume summary + bullet points + a cover letter.
"""
        output = call_openai("You are an expert HR writer.", prompt)
        st.write(output)

# ----------------- 3️⃣ BLOG WRITER -----------------
elif mode == "Blog Writer":
    st.subheader("✍️ Blog Writer")
    topic = st.text_input("Blog Topic")

    if st.button("Generate Blog"):
        output = call_openai("You are a blog expert.", f"Write a blog on: {topic}")
        st.write(output)

# ----------------- 4️⃣ EMAIL -----------------
elif mode == "Email Writer":
    st.subheader("📧 Email Writer")
    purpose = st.text_input("Purpose")
    context = st.text_area("Context")

    if st.button("Generate Email"):
        output = call_openai("You write professional emails.", f"{purpose}\n{context}")
        st.write(output)

# ----------------- 5️⃣ CODE -----------------
elif mode == "Code Helper":
    st.subheader("💻 Code Helper")
    code = st.text_area("Paste your code")

    if st.button("Explain Code"):
        output = call_openai("You are a senior developer.", f"Explain this code:\n{code}")
        st.write(output)
