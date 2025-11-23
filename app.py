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

# free requests per session (can override from Streamlit secrets / env)
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 10))

# single access code for now (manual distribution after Razorpay payment)
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
    """Check if user is allowed to make another request."""
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"You have reached the free limit of {FREE_DAILY_LIMIT} requests "
            "for this session.\n\nUpgrade to premium to continue using "
            f"{APP_NAME} without limits."
        )
        return False
    return True


def register_request() -> None:
    """Increase usage counter for non-premium users."""
    if not st.session_state.is_premium:
        st.session_state.request_count += 1


def call_openai(system_prompt: str, user_prompt: str) -> str | None:
    """Generic helper for one-shot tasks (non-chat-history)."""
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


# ---------- Sidebar: Branding, Theme, Account ----------
st.sidebar.title(APP_NAME)

# Theme toggle (simple CSS based). Default: Light.
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
if theme == "Dark":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #111827;
            color: #e5e7eb;
        }
        .stTextInput, .stTextArea, .stSelectbox {
            color: #111827;
        }
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

# Account / usage info
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

# Simple usage progress bar for free users
if not st.session_state.is_premium:
    progress_value = (
        st.session_state.request_count / FREE_DAILY_LIMIT
        if FREE_DAILY_LIMIT > 0
        else 0
    )
    st.sidebar.progress(progress_value)

# Premium unlock section
with st.sidebar.expander("Have a premium access code?"):
    code_input = st.text_input("Enter access code", type="password")
    unlock_clicked = st.button("Unlock premium", use_container_width=True)
    if unlock_clicked:
        if code_input and code_input == PREMIUM_ACCESS_CODE:
            st.session_state.is_premium = True
            st.session_state.request_count = 0
            st.session_state.premium_activated_at = datetime.utcnow().isoformat()
            st.success("🎉 Premium unlocked for this browser session.")
        elif code_input:
            st.error("Incorrect access code. Please check and try again.")

st.sidebar.write("---")

# Payment info
st.sidebar.subheader("Upgrade to premium")

st.sidebar.write(
    "Use the link below to pay securely. After payment, you’ll receive "
    "your premium access code. Enter it above to unlock unlimited usage."
)

st.sidebar.markdown(
    "[💳 Pay with Razorpay (UPI / Cards)]"
    "(https://razorpay.me/@rochvincentrajinfantmychiline)"
)

st.sidebar.caption(
    "Supported options for you as the owner:\n"
    "- Razorpay payment page (UPI, cards, wallets)\n"
    "- (Optional) Stripe checkout link\n"
    "- (Optional) PayPal.me link"
)

st.sidebar.write("---")
st.sidebar.write("Tip: Start with one mode to earn, then expand.")


# ---------- Main header ----------
st.title(APP_NAME)
st.caption("Multi-skill AI assistant built with OpenAI + Streamlit.")

st.write(
    "Use the sidebar to pick what you want help with: chatting, resumes, "
    "content, emails, or coding. Free users have a limited number of "
    "requests per session; premium users get unlimited access."
)


# ================== MODES ================== #

# 1. General Chat
if mode == "General Chat":
    st.subheader("💬 General Chat Assistant")
    st.write(
        "Ask anything: concepts, explanations, ideas, planning, or casual questions."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        user_message = st.text_area("Type your message:", height=150, key="chat_box")
    with col2:
        send_clicked = st.button("Send", use_container_width=True)
        clear_clicked = st.button("Clear chat history", use_container_width=True)

    if clear_clicked:
        st.session_state.chat_history = []
        st.success("Chat history cleared.")

    if send_clicked:
        if not user_message.strip():
            st.warning("Please type something first.")
        else:
            st.session_state.chat_history.append(("You", user_message))

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful, friendly AI assistant.",
                }
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
        st.info("Start the conversation by typing a message above.")
    else:
        for speaker, msg in st.session_state.chat_history:
            if speaker == "You":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 AI:** {msg}")


# 2. Resume & Cover Letter
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter Assistant")
    st.write(
        "Get a sharp resume summary, bullet points, and a tailored cover letter "
        "for any role."
    )

    name = st.text_input("Your Name")
    role = st.text_input(
        "Target Job Role (for example, Python Developer, Data Analyst)"
    )
    skills = st.text_area("Skills (comma separated)", "Python, SQL, Machine Learning")
    projects = st.text_area("Projects (briefly describe)")
    experience = st.text_area("Internships / Experience")
    extras = st.text_area("Extra info (certificates, hackathons, achievements)")
    tone = st.selectbox("Tone", ["Professional", "Friendly professional", "Very formal"])

    if st.button("Generate Resume Summary & Cover Letter", use_container_width=True):
        if not role.strip():
            st.warning("Please at least provide a target job role.")
        else:
            user_prompt = f"""
Name: {name}
Target Role: {role}
Skills: {skills}
Projects: {projects}
Experience: {experience}
Extra Info: {extras}
Preferred tone: {tone}

Tasks:
1. Write a 3–4 line professional summary for my resume.
2. Create 5–7 bullet points combining skills, projects, and experience.
3. Write a 200–250 word cover letter tailored to the target role.

Do not invent fake experience. If something is missing, be honest but positive.
"""
            system_prompt = (
                "You are an expert HR and resume writer. "
                "Your job is to help job seekers craft strong, honest resumes "
                "and cover letters."
            )

            with st.spinner("Creating resume content..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.subheader("Generated Content")
                st.write(output)


# 3. Blog / Social Post Writer
elif mode == "Blog / Social Post Writer":
    st.subheader("✍️ Blog and Social Media Content Writer")
    st.write(
        "Generate high-quality posts for blogs, LinkedIn, Instagram, or X (Twitter)."
    )

    content_type = st.selectbox(
        "Content type",
        ["Blog Post", "LinkedIn Post", "Instagram Caption", "Twitter or X Thread"],
    )
    topic = st.text_input("Topic or Title")
    audience = st.text_input(
        "Target Audience (for example, freshers, small business owners)"
    )
    length = st.selectbox("Length", ["Short", "Medium", "Long"])
    extras = st.text_area("Extra instructions (tone, language, call to action, etc.)")

    if st.button("Generate Content", use_container_width=True):
        if not topic.strip():
            st.warning("Please provide at least a topic or title.")
        else:
            user_prompt = f"""
Content type: {content_type}
Topic: {topic}
Target audience: {audience}
Length: {length}
Extra instructions: {extras}

Write high-quality, original content that is helpful and engaging for the audience.
Avoid generic fluff; give practical value, structure, and a clear message.
"""
            system_prompt = (
                "You are an expert content writer and social media marketer. "
                "You write clear, engaging content tailored to the audience."
            )

            with st.spinner("Writing content..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.subheader("Generated Content")
                st.write(output)


# 4. Email Writer
elif mode == "Email Writer":
    st.subheader("📧 Professional Email Writer")
    st.write(
        "Draft clear, polite, professional emails for different situations in seconds."
    )

    email_purpose = st.selectbox(
        "Email purpose",
        [
            "Job Application",
            "Follow-up after Interview",
            "Cold Email to Client",
            "Networking or Connection Request",
            "General Professional Email",
        ],
    )
    to_whom = st.text_input("Recipient (for example, HR, Manager, Client)")
    context = st.text_area("Context or Details (what is this email about?)")
    style = st.selectbox("Tone", ["Formal", "Semi-formal", "Friendly professional"])

    if st.button("Generate Email", use_container_width=True):
        if not context.strip():
            st.warning("Please provide some context so the email is accurate.")
        else:
            user_prompt = f"""
Purpose: {email_purpose}
Recipient: {to_whom}
Context: {context}
Tone: {style}

Write a clear, polite, professional email. Include both a subject line and the email body.
"""
            system_prompt = (
                "You are an expert at writing professional emails that are polite, "
                "clear, and effective."
            )

            with st.spinner("Drafting email..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.subheader("Email Draft")
                st.write(output)


# 5. Code Helper
elif mode == "Code Helper":
    st.subheader("💻 Coding Helper")
    st.write(
        "Paste your code or describe the problem. "
        "You’ll get an explanation plus improved code with comments."
    )

    language = st.selectbox(
        "Language", ["Python", "JavaScript", "C++", "Java", "Other"]
    )
    help_type = st.selectbox(
        "What do you need?",
        ["Explain code", "Fix bug", "Write new function", "Optimize or refactor"],
    )
    code_or_desc = st.text_area("Paste your code or describe what you need", height=200)

    if st.button("Get Coding Help", use_container_width=True):
        if not code_or_desc.strip():
            st.warning("Please paste some code or describe your issue.")
        else:
            user_prompt = f"""
Language: {language}
Help type: {help_type}
Code or Description:
{code_or_desc}

Explain step by step, then give the improved or fixed code if relevant.
Add comments in the code to help a beginner understand.
"""
            system_prompt = (
                "You are a patient senior developer and teacher. "
                "You explain concepts clearly for beginners and provide correct, "
                "clean solutions."
            )

            with st.spinner("Thinking about your code..."):
                output = call_openai(system_prompt, user_prompt)

            if output:
                st.subheader("Help and Solution")
                st.write(output)

