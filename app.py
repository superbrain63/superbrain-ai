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
# Brand Logo (MUST exist in the repo)
# ---------------------------------------------------
# Put "SuperBrain.png" in the SAME folder as app.py
st.image("SuperBrain.png", width=160)

# ---------------------------------------------------
# OpenAI API Setup
# ---------------------------------------------------
api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key:
    st.error(
        "🚨 No OpenAI API key found.\n\n"
        "Add `OPENAI_API_KEY` to your `.env` (local) or Streamlit Secrets (deployed)."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ---------------------------------------------------
# Billing / plan settings
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

if "premium_activated_at" not in st.session_state:
    st.session_state.premium_activated_at = None

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------
def can_use_ai():
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"⚠️ Free limit reached ({FREE_DAILY_LIMIT} requests).\n"
            "Upgrade to premium for **unlimited access**."
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
        return f"❌ OpenAI Error: {e}"


# ---------------------------------------------------
# Sidebar UI
# ---------------------------------------------------
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
    ["General Chat", "Resume & Cover Letter", "Blog Writer", "Email Writer", "Code Helper"],
)

st.sidebar.subheader("Usage")

remaining = (
    "Unlimited"
    if st.session_state.is_premium
    else FREE_DAILY_LIMIT - st.session_state.request_count
)

st.sidebar.write(f"Requests Used: {st.session_state.request_count}")
st.sidebar.write(f"Remaining: {remaining}")

if not st.session_state.is_premium:
    st.sidebar.progress(st.session_state.request_count / FREE_DAILY_LIMIT)

# ---------------------------------------------------
# Premium Unlock Section
# ---------------------------------------------------
st.sidebar.subheader("🔑 Have a Premium Code?")
code_input = st.sidebar.text_input("Enter Code", type="password")

if st.sidebar.button("Unlock Premium"):
    if code_input == PREMIUM_ACCESS_CODE:
        st.session_state.is_premium = True
        st.session_state.request_count = 0
        st.success("🎉 Premium Unlocked — Enjoy Unlimited Access!")
    else:
        st.error("❌ Incorrect Code.")

st.sidebar.write("---")
st.sidebar.subheader("💳 Upgrade to Premium")

st.sidebar.markdown(
    "[Pay ₹299 on Razorpay](https://rzp.io/rzp/HuxrI9w)"
)

st.sidebar.caption("Your premium access code will be emailed automatically.")


# ---------------------------------------------------
# Main Header
# ---------------------------------------------------
st.title(APP_NAME)
st.caption("Your multi-skill AI assistant powered by OpenAI + Streamlit.")


# ---------------------------------------------------
# TOOL 1 — General Chat
# ---------------------------------------------------
if mode == "General Chat":
    st.subheader("💬 Chat with AI")

    user_msg = st.text_area("Type your message:")

    if st.button("Send"):
        if user_msg.strip():
            st.session_state.chat_history.append(("You", user_msg))

            messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
            for speaker, msg in st.session_state.chat_history:
                role = "user" if speaker == "You" else "assistant"
                messages.append({"role": role, "content": msg})

            if can_use_ai():
                try:
                    reply = client.chat.completions.create(
                        model="gpt-4o-mini", messages=messages
                    ).choices[0].message.content

                    st.session_state.chat_history.append(("AI", reply))
                    register_request()

                except Exception as e:
                    st.error(e)

    st.write("---")
    for speaker, msg in st.session_state.chat_history:
        st.markdown(f"**{speaker}:** {msg}")


# ---------------------------------------------------
# TOOL 2 — Resume & Cover Letter
# ---------------------------------------------------
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter Builder")

    name = st.text_input("Your Name")
    role = st.text_input("Job Role")
    skills = st.text_area("Skills")
    projects = st.text_area("Projects")
    experience = st.text_area("Experience")

    if st.button("Generate"):
        prompt = f"""
Create:
1. A strong resume summary.
2. 6 bullet points using skills/projects/experience.
3. A professional cover letter.

Name: {name}
Role: {role}
Skills: {skills}
Projects: {projects}
Experience: {experience}
"""
        output = call_openai("You are an HR expert.", prompt)
        st.write(output)


# ---------------------------------------------------
# TOOL 3 — Blog Writer
# ---------------------------------------------------
elif mode == "Blog Writer":
    st.subheader("✍️ Blog Writer")

    topic = st.text_input("Topic")

    if st.button("Generate Blog"):
        output = call_openai("You are a blog expert.", f"Write a blog about: {topic}")
        st.write(output)


# ---------------------------------------------------
# TOOL 4 — Email Writer
# ---------------------------------------------------
elif mode == "Email Writer":
    st.subheader("📧 Professional Email Writer")

    purpose = st.text_input("Email Purpose")
    details = st.text_area("Details / Context")

    if st.button("Generate Email"):
        output = call_openai(
            "You are an expert at writing clear professional emails.",
            f"Write an email for the purpose: {purpose}\nDetails: {details}",
        )
        st.write(output)


# ---------------------------------------------------
# TOOL 5 — Code Helper
# ---------------------------------------------------
elif mode == "Code Helper":
    st.subheader("💻 Code Helper")

    code_text = st.text_area("Paste your code here")

    if st.button("Explain Code"):
        output = call_openai(
            "You are a senior software engineer.",
            f"Explain this code clearly:\n{code_text}",
        )
        st.write(output)
