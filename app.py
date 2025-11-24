import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Load environment variables ----------
load_dotenv()

st.set_page_config(page_title="SuperBrain AI", layout="wide")

# ---------- Display Logo (Correct & Only One) ----------
# Make sure "Super Brain.png" is in same folder as app.py
st.markdown(
    """
    <div style="text-align:center; margin-top:10px; margin-bottom:5px;">
        <img src="Super Brain.png" width="160">
    </div>
    """,
    unsafe_allow_html=True,
)

api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key:
    st.error(
        "No OpenAI API key found.\n\n"
        "Set OPENAI_API_KEY in your .env file (local) or in Streamlit Secrets (cloud)."
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
# PREMIUM BANNER (NO IMAGES)
# ============================
if st.session_state.is_premium:
    st.markdown(
        """
        <div style="text-align:center; 
                    background:#4f46e5; 
                    color:#fff;
                    padding:6px 14px;
                    border-radius:10px;
                    width:200px;
                    margin:auto;
                    margin-bottom:15px;">
            ✨ Premium User — Unlimited Access
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div style="text-align:center; 
                    background:#f59e0b; 
                    color:#fff;
                    padding:6px 14px;
                    border-radius:10px;
                    width:230px;
                    margin:auto;
                    margin-bottom:15px;">
            ⚡ Free User — Limited Access
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------
# Helper Functions
# --------------------------------
def can_use_ai():
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"Free limit reached ({FREE_DAILY_LIMIT} requests). Upgrade to Premium."
        )
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
        return f"❌ Error: {e}"


# ============================
# SIDEBAR UI
# ============================
st.sidebar.title(APP_NAME)

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>.stApp { background-color:#0D1117; color:#E6EDF3; }</style>
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

# Usage Panel
st.sidebar.subheader("Usage")
remaining = (
    "Unlimited"
    if st.session_state.is_premium
    else FREE_DAILY_LIMIT - st.session_state.request_count
)
st.sidebar.write(f"Used: {st.session_state.request_count}")
st.sidebar.write(f"Remaining: {remaining}")

if not st.session_state.is_premium:
    st.sidebar.progress(st.session_state.request_count / FREE_DAILY_LIMIT)

# Premium unlock
st.sidebar.subheader("🔑 Have a Premium Code?")
code_in = st.sidebar.text_input("Enter Access Code", type="password")
if st.sidebar.button("Unlock Premium"):
    if code_in == PREMIUM_ACCESS_CODE:
        st.session_state.is_premium = True
        st.session_state.request_count = 0
        st.success("🎉 Premium Unlocked!")
    else:
        st.error("❌ Wrong code")

st.sidebar.write("---")

st.sidebar.subheader("💳 Upgrade to Premium")
st.sidebar.markdown("[Pay ₹299 on Razorpay](https://rzp.io/rzp/HuxrI9w)")
st.sidebar.caption("You will receive a premium access code via email.")


# ============================
# MAIN CONTENT
# ============================
st.title(APP_NAME)
st.caption("Your multi-skill AI assistant powered by OpenAI + Streamlit.")


# ----------------------------------
# 1️⃣ General Chat
# ----------------------------------
if mode == "General Chat":
    st.subheader("💬 Chat with AI")

    user_msg = st.text_area("Enter message:")

    if st.button("Send"):
        if user_msg.strip():
            st.session_state.chat_history.append(("You", user_msg))

            messages = [{"role": "system", "content": "You are a helpful AI."}]
            for role, msg in st.session_state.chat_history:
                messages.append(
                    {"role": "user" if role == "You" else "assistant", "content": msg}
                )

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
# 2️⃣ Resume Maker
# ----------------------------------
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter")

    name = st.text_input("Name")
    role = st.text_input("Job Role")
    skills = st.text_area("Skills")
    exp = st.text_area("Experience")
    projects = st.text_area("Projects")

    if st.button("Generate"):
        prompt = f"""
Create resume + cover letter.

Name: {name}
Role: {role}
Skills: {skills}
Experience: {exp}
Projects: {projects}
"""
        output = call_openai("You are HR expert.", prompt)
        st.write(output)


# ----------------------------------
# 3️⃣ Blog Writer
# ----------------------------------
elif mode == "Blog / Social Post Writer":
    st.subheader("✍️ Blog Writer")

    topic = st.text_input("Topic")
    if st.button("Generate Blog"):
        output = call_openai("You are blog expert.", f"Write a blog about {topic}")
        st.write(output)


# ----------------------------------
# 4️⃣ Email Writer
# ----------------------------------
elif mode == "Email Writer":
    st.subheader("📧 Email Writer")

    purpose = st.text_input("Purpose")
    context = st.text_area("Context")

    if st.button("Generate Email"):
        output = call_openai(
            "You write professional emails.",
            f"Purpose: {purpose}\nContext: {context}",
        )
        st.write(output)


# ----------------------------------
# 5️⃣ Code Helper
# ----------------------------------
elif mode == "Code Helper":
    st.subheader("💻 Code Helper")

    code_text = st.text_area("Paste your code")

    if st.button("Explain Code"):
        output = call_openai("You are a senior developer.", f"Explain:\n{code_text}")
        st.write(output)
