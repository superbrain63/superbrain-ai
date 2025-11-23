import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Load environment variables ----------
load_dotenv()

st.set_page_config(page_title="SuperBrain AI", layout="wide")

api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key:
    st.error(
        "No OpenAI API key found.\n\n"
        "Set OPENAI_API_KEY in your .env file (for local) "
        "or in Streamlit Cloud Secrets (for deployed app)."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ---------- Billing / plan settings ----------
APP_NAME = "SuperBrain AI"

FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 10))

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


# ---------- Helper functions ----------
def can_use_ai() -> bool:
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"You have reached the free limit of {FREE_DAILY_LIMIT} requests.\n"
            f"Upgrade to premium to use {APP_NAME} without limits."
        )
        return False
    return True


def register_request() -> None:
    if not st.session_state.is_premium:
        st.session_state.request_count += 1


def call_openai(system_prompt: str, user_prompt: str) -> str | None:
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
        return f"Error calling OpenAI API: {e}"


# ---------- Sidebar ----------
st.sidebar.title(APP_NAME)

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
if theme == "Dark":
    st.markdown(
        """
        <style>
        .stApp { background-color: #111827; color: #e5e7eb; }
        </style>
        """,
        unsafe_allow_html=True,
    )

mode = st.sidebar.selectbox(
    "Choose what you want the AI to do:",
    [
        "General Chat",
        "Resume & Cover Letter",
        "Blog / Social Post Writer",
        "Email Writer",
        "Code Helper",
    ],
)

st.sidebar.write("---")

# Account status
st.sidebar.subheader("Account & Usage")

status_text = "Premium user" if st.session_state.is_premium else "Free user"
if st.session_state.is_premium:
    st.sidebar.success(status_text)
else:
    st.sidebar.info(status_text)

remaining = (
    "Unlimited"
    if st.session_state.is_premium
    else max(FREE_DAILY_LIMIT - st.session_state.request_count, 0)
)

st.sidebar.write(f"Free limit per session: {FREE_DAILY_LIMIT}")
st.sidebar.write(f"Requests used: {st.session_state.request_count}")
st.sidebar.write(f"Requests remaining: {remaining}")

if not st.session_state.is_premium:
    progress_value = (
        st.session_state.request_count / FREE_DAILY_LIMIT
        if FREE_DAILY_LIMIT > 0
        else 0
    )
    st.sidebar.progress(progress_value)

# Premium unlock
with st.sidebar.expander("Have a premium access code?"):
    code_input = st.text_input("Enter access code", type="password")
    unlock_clicked = st.button("Unlock premium", use_container_width=True)
    if unlock_clicked:
        if code_input == PREMIUM_ACCESS_CODE:
            st.session_state.is_premium = True
            st.session_state.request_count = 0
            st.session_state.premium_activated_at = datetime.utcnow().isoformat()
            st.success("🎉 Premium unlocked for this browser session!")
        else:
            st.error("Incorrect access code.")

st.sidebar.write("---")

# Upgrade section
st.sidebar.subheader("Upgrade to premium")

st.sidebar.write(
    "Get **unlimited access** to SuperBrain AI.\n"
    "Click below to pay securely via Razorpay.\n\n"
    "After payment, you'll receive your **10-digit Premium Code** by email."
)

st.sidebar.markdown(
    "[💳 Upgrade Now — ₹299/month](https://rzp.io/rzp/HuxrI9w)"
)

st.sidebar.caption(
    "Payments supported: UPI, Cards, Netbanking.\n"
    "Enter the received Premium Code above to unlock unlimited access."
)

st.sidebar.write("---")

# ---------- Main UI ----------
st.title(APP_NAME)
st.caption("Multi-skill AI assistant powered by OpenAI + Streamlit.")

st.write(
    "Pick a mode from the sidebar. Free users get limited daily requests; "
    "premium users enjoy unlimited access."
)

# ================== MODES ================== #

# 1. General Chat
if mode == "General Chat":
    st.subheader("💬 General Chat Assistant")

    col1, col2 = st.columns([3, 1])
    with col1:
        user_message = st.text_area("Type your message:", height=150, key="chat_box")
    with col2:
        send_clicked = st.button("Send", use_container_width=True)
        clear_clicked = st.button("Clear History", use_container_width=True)

    if clear_clicked:
        st.session_state.chat_history = []
        st.success("Chat history cleared.")

    if send_clicked:
        if not user_message.strip():
            st.warning("Type something first.")
        else:
            st.session_state.chat_history.append(("You", user_message))

            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]

            for speaker, msg in st.session_state.chat_history:
                role = "user" if speaker == "You" else "assistant"
                messages.append({"role": role, "content": msg})

            if can_use_ai():
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                    )
                    reply = response.choices[0].message.content
                    register_request()
                except Exception as e:
                    reply = f"Error: {e}"

                st.session_state.chat_history.append(("AI", reply))

    st.write("---")
    st.markdown("#### Conversation")
    if not st.session_state.chat_history:
        st.info("Start a conversation above.")
    else:
        for speaker, msg in st.session_state.chat_history:
            if speaker == "You":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 AI:** {msg}")


# 2. Resume Writer
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter Assistant")
    st.write("Generate professional resumes and cover letters.")

    name = st.text_input("Your Name")
    role = st.text_input("Target Role")
    skills = st.text_area("Skills (comma separated)")
    projects = st.text_area("Projects")
    experience = st.text_area("Experience")
    extras = st.text_area("Extras")
    tone = st.selectbox("Tone", ["Professional", "Friendly", "Very formal"])

    if st.button("Generate", use_container_width=True):
        if not role.strip():
            st.warning("Enter a target role.")
        else:
            user_prompt = f"""
Name: {name}
Role: {role}
Skills: {skills}
Projects: {projects}
Experience: {experience}
Extras: {extras}
Tone: {tone}

Create a resume summary, 5–7 bullet points, and a 200-word cover letter.
"""
            system_prompt = "You are an expert HR assistant."

            with st.spinner("Generating..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.write(output)


# 3. Blog Writer
elif mode == "Blog / Social Post Writer":
    st.subheader("✍️ Blog / Social Content Writer")

    content_type = st.selectbox(
        "Content type",
        ["Blog Post", "LinkedIn Post", "Instagram Caption", "Twitter Thread"],
    )
    topic = st.text_input("Topic")
    audience = st.text_input("Audience")
    length = st.selectbox("Length", ["Short", "Medium", "Long"])
    extras = st.text_area("Extra instructions")

    if st.button("Generate", use_container_width=True):
        if not topic.strip():
            st.warning("Enter a topic.")
        else:
            user_prompt = f"""
Type: {content_type}
Topic: {topic}
Audience: {audience}
Length: {length}
Extras: {extras}

Write high-quality, structured content.
"""
            system_prompt = "You are an expert content writer."

            with st.spinner("Generating..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.write(output)


# 4. Email Writer
elif mode == "Email Writer":
    st.subheader("📧 Email Writer")

    email_purpose = st.selectbox(
        "Purpose",
        [
            "Job Application",
            "Interview Follow-up",
            "Cold Email",
            "Networking",
            "General Email",
        ],
    )
    to_whom = st.text_input("Recipient")
    context = st.text_area("Context")
    style = st.selectbox("Tone", ["Formal", "Semi-formal", "Friendly"])

    if st.button("Generate Email", use_container_width=True):
        if not context.strip():
            st.warning("Enter context.")
        else:
            user_prompt = f"""
Purpose: {email_purpose}
Recipient: {to_whom}
Context: {context}
Tone: {style}
Write subject + email body.
"""
            system_prompt = "You write perfect professional emails."

            with st.spinner("Generating..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.write(output)


# 5. Code Helper
elif mode == "Code Helper":
    st.subheader("💻 Code Helper")

    language = st.selectbox("Language", ["Python", "JavaScript", "C++", "Java", "Other"])
    help_type = st.selectbox(
        "Need help with:",
        ["Explain code", "Fix bug", "Write new function", "Optimize code"],
    )
    code_or_desc = st.text_area("Paste code or describe issue", height=200)

    if st.button("Get Help", use_container_width=True):
        if not code_or_desc.strip():
            st.warning("Enter code or description.")
        else:
            user_prompt = f"""
Language: {language}
Help type: {help_type}
Code:
{code_or_desc}

Explain step by step and provide improved code.
"""
            system_prompt = "You are a senior developer."

            with st.spinner("Thinking..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.write(output)
