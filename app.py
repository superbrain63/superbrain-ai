import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# =====================================
# Load environment & API key
# =====================================
load_dotenv()

st.set_page_config(page_title="SuperBrain AI", layout="wide")

# Show logo (file must be in same folder as app.py)
st.image("Super Brain.png", width=160)

api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key:
    st.error(
        "No OpenAI API key found.\n\n"
        "Set OPENAI_API_KEY in your .env file (for local runs) "
        "or in Streamlit Cloud Secrets (for deployed app)."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# =====================================
# App / billing configuration
# =====================================
APP_NAME = "SuperBrain AI"
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 5))
PREMIUM_ACCESS_CODE = os.getenv("PREMIUM_ACCESS_CODE", "")

# =====================================
# Session state initialisation
# =====================================
ss = st.session_state

if "request_count" not in ss:         # free requests counter (this session)
    ss.request_count = 0

if "is_premium" not in ss:
    ss.is_premium = False

if "chat_history" not in ss:
    ss.chat_history = []             # list of tuples (role, message)

if "premium_activated_at" not in ss:
    ss.premium_activated_at = None

if "show_premium_modal" not in ss:
    ss.show_premium_modal = False

# Simple usage analytics
if "analytics" not in ss:
    ss.analytics = {
        "total_requests": 0,
        "free_requests": 0,
        "premium_requests": 0,
        "per_mode": {},              # mode -> count
        "first_use_at": datetime.utcnow().isoformat(),
    }

# =====================================
# Global styles (chat bubbles + modal)
# =====================================
st.markdown(
    """
    <style>
        /* Chat bubbles */
        .chat-container {
            max-width: 900px;
            margin: 0 auto;
        }
        .chat-bubble-user {
            background: #2563EB;
            color: white;
            padding: 10px 14px;
            border-radius: 18px;
            margin: 6px 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .chat-bubble-ai {
            background: #F3F4F6;
            color: #111827;
            padding: 10px 14px;
            border-radius: 18px;
            margin: 6px 0;
            max-width: 80%;
            margin-right: auto;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }
        .chat-label {
            font-size: 12px;
            opacity: 0.7;
            margin-bottom: -2px;
        }

        /* Premium badge */
        .premium-badge {
            text-align: center;
            background: linear-gradient(90deg, #4f46e5, #9333ea);
            color: white;
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 14px;
            display: inline-block;
            margin-bottom: 16px;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
        }
        .free-badge {
            text-align: center;
            background: #f59e0b;
            color: white;
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 14px;
            display: inline-block;
            margin-bottom: 16px;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
        }

        /* Fake modal overlay */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15,23,42,0.65);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        .modal-box {
            background: #111827;
            color: #E5E7EB;
            padding: 24px 26px;
            border-radius: 16px;
            max-width: 430px;
            box-shadow: 0 20px 45px rgba(0,0,0,0.4);
        }
        .modal-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .modal-sub {
            font-size: 13px;
            opacity: 0.8;
            margin-bottom: 16px;
        }
        .modal-price {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .modal-small {
            font-size: 12px;
            opacity: 0.8;
        }
        .modal-btn-row {
            margin-top: 18px;
            display: flex;
            gap: 10px;
        }
        .modal-btn-row button {
            flex: 1;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================
# Helper functions
# =====================================
def _bump_analytics(mode: str) -> None:
    """Update analytics counters."""
    ss.analytics["total_requests"] += 1
    ss.analytics["per_mode"][mode] = ss.analytics["per_mode"].get(mode, 0) + 1

    if ss.is_premium:
        ss.analytics["premium_requests"] += 1
    else:
        ss.analytics["free_requests"] += 1


def can_use_ai(mode: str) -> bool:
    """Check if user can make another request."""
    if ss.is_premium:
        return True

    if ss.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"⚠️ You’ve reached the free limit of {FREE_DAILY_LIMIT} requests "
            "for this session.\n\nUpgrade to premium for unlimited access."
        )
        # Trigger modal popup
        ss.show_premium_modal = True
        return False
    return True


def register_request(mode: str) -> None:
    """Increase usage counter for non-premium users and analytics."""
    if not ss.is_premium:
        ss.request_count += 1
    _bump_analytics(mode)


def call_openai(system_prompt: str, user_prompt: str, mode: str) -> str | None:
    """Generic helper for one-shot tasks (non-chat-history)."""
    if not can_use_ai(mode):
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        register_request(mode)
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error calling OpenAI API: {e}"


# =====================================
# Sidebar UI
# =====================================
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
        "Usage Analytics",
    ],
)

st.sidebar.subheader("Usage")
remaining = (
    "Unlimited"
    if ss.is_premium
    else max(FREE_DAILY_LIMIT - ss.request_count, 0)
)
st.sidebar.write(f"Requests used: {ss.request_count}")
st.sidebar.write(f"Remaining: {remaining}")

if not ss.is_premium:
    st.sidebar.progress(
        ss.request_count / FREE_DAILY_LIMIT if FREE_DAILY_LIMIT else 0
    )

# Premium unlock
st.sidebar.subheader("🔑 Have a Premium Code?")
input_code = st.sidebar.text_input("Enter Access Code", type="password")
if st.sidebar.button("Unlock Premium"):
    if input_code.strip() and input_code.strip() == PREMIUM_ACCESS_CODE:
        ss.is_premium = True
        ss.request_count = 0
        ss.premium_activated_at = datetime.utcnow().isoformat()
        st.success("🎉 Premium Unlocked — Enjoy Unlimited Access!")
    else:
        st.error("❌ Invalid access code. Please check and try again.")

# Upgrade section only for free users (watermark removal)
if not ss.is_premium:
    st.sidebar.write("---")
    st.sidebar.subheader("💳 Upgrade to Premium")
    st.sidebar.markdown(
        "[Pay ₹299 on Razorpay](https://rzp.io/rzp/HuxrI9w)"
    )
    st.sidebar.caption(
        "After payment, your premium access code will be emailed to you."
    )
    if st.sidebar.button("Learn about Premium"):
        ss.show_premium_modal = True


# =====================================
# Premium popup modal (fake overlay)
# =====================================
if ss.show_premium_modal and not ss.is_premium:
    with st.container():
        st.markdown(
            """
            <div class="modal-overlay">
                <div class="modal-box">
                    <div class="modal-title">Unlock SuperBrain AI Premium</div>
                    <div class="modal-sub">
                        Unlimited chats • No usage limits • Priority quality.
                    </div>
                    <div class="modal-price">₹299 / month</div>
                    <div class="modal-small">
                        Secure payment via Razorpay. You’ll receive a unique premium
                        access code in your email after payment. Enter it in the left
                        sidebar to unlock.
                    </div>
                    <div class="modal-small" style="margin-top:10px;">
                        ✔ Unlimited AI requests<br>
                        ✔ All tools included (chat, resumes, blogs, email, code)<br>
                        ✔ Best for students & professionals
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💳 Pay with Razorpay", key="modal_pay"):
            st.markdown(
                "[Click here to pay ₹299](https://rzp.io/rzp/HuxrI9w)",
                unsafe_allow_html=True,
            )
    with col_b:
        if st.button("Close", key="modal_close"):
            ss.show_premium_modal = False


# =====================================
# Main header + badges
# =====================================
st.title(APP_NAME)
if ss.is_premium:
    st.markdown(
        '<div class="premium-badge">✨ Premium User — Unlimited Access</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="free-badge">⚡ Free User — Limited Access</div>',
        unsafe_allow_html=True,
    )

st.caption("Your multi-skill AI assistant powered by OpenAI + Streamlit.")


# =====================================
# MODES
# =====================================

# ---------- 1. General Chat ----------
if mode == "General Chat":
    st.subheader("💬 Chat with AI")

    col1, col2 = st.columns([4, 1])
    with col1:
        user_msg = st.text_area("Type your message:", key="chat_input", height=120)
    with col2:
        send_clicked = st.button("Send", use_container_width=True)
        clear_clicked = st.button("Clear chat", use_container_width=True)

    if clear_clicked:
        ss.chat_history = []
        st.success("Chat history cleared.")

    if send_clicked:
        if user_msg.strip():
            ss.chat_history.append(("You", user_msg))

            # Build messages for OpenAI
            messages = [{"role": "system", "content": "You are a helpful, friendly AI assistant."}]
            for speaker, msg in ss.chat_history:
                role = "user" if speaker == "You" else "assistant"
                messages.append({"role": role, "content": msg})

            if can_use_ai("General Chat"):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                    )
                    reply = response.choices[0].message.content
                    register_request("General Chat")
                    ss.chat_history.append(("AI", reply))
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please type a message before sending.")

    # Chat bubbles UI
    st.write("---")
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    if not ss.chat_history:
        st.info("Start the conversation by typing a message above.")
    else:
        for speaker, msg in ss.chat_history:
            if speaker == "You":
                st.markdown(
                    f"""
                    <div class="chat-bubble-user">
                        <div class="chat-label">You</div>
                        <div>{msg}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="chat-bubble-ai">
                        <div class="chat-label">SuperBrain AI</div>
                        <div>{msg}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- 2. Resume & Cover Letter ----------
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter Assistant")

    name = st.text_input("Your Name")
    role = st.text_input("Target Job Role (e.g., Python Developer)")
    skills = st.text_area("Skills (comma-separated)", "Python, SQL, Machine Learning")
    projects = st.text_area("Projects (briefly describe)")
    experience = st.text_area("Internships / Experience")
    extras = st.text_area("Extra info (certificates, hackathons, achievements)")
    tone = st.selectbox("Tone", ["Professional", "Friendly professional", "Very formal"])

    if st.button("Generate Resume Summary & Cover Letter"):
        if not role.strip():
            st.warning("Please provide at least a target job role.")
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
"""
            system_prompt = (
                "You are an expert HR and resume writer. You help job seekers craft "
                "strong, honest resumes and cover letters."
            )
            with st.spinner("Creating resume content..."):
                output = call_openai(system_prompt, user_prompt, "Resume & Cover Letter")

            if output:
                st.subheader("Generated Content")
                st.write(output)


# ---------- 3. Blog / Social Post Writer ----------
elif mode == "Blog / Social Post Writer":
    st.subheader("✍️ Blog & Social Media Content Writer")

    content_type = st.selectbox(
        "Content type",
        ["Blog Post", "LinkedIn Post", "Instagram Caption", "Twitter / X Thread"],
    )
    topic = st.text_input("Topic or Title")
    audience = st.text_input("Target Audience", "Students, Freshers, etc.")
    length = st.selectbox("Length", ["Short", "Medium", "Long"])
    extras = st.text_area("Extra instructions (tone, language, CTA, etc.)")

    if st.button("Generate Content"):
        if not topic.strip():
            st.warning("Please provide a topic or title.")
        else:
            user_prompt = f"""
Content type: {content_type}
Topic: {topic}
Target audience: {audience}
Length: {length}
Extra instructions: {extras}

Write high-quality, original content that is helpful and engaging for the audience.
Avoid generic fluff; give practical value and clear structure.
"""
            system_prompt = (
                "You are an expert content writer and social media marketer."
            )
            with st.spinner("Writing content..."):
                output = call_openai(system_prompt, user_prompt, "Blog / Social Post Writer")

            if output:
                st.subheader("Generated Content")
                st.write(output)


# ---------- 4. Email Writer ----------
elif mode == "Email Writer":
    st.subheader("📧 Professional Email Writer")

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
    to_whom = st.text_input("Recipient (HR, Manager, Client, etc.)")
    context = st.text_area("Context / Details")
    style = st.selectbox("Tone", ["Formal", "Semi-formal", "Friendly professional"])

    if st.button("Generate Email"):
        if not context.strip():
            st.warning("Please provide some context.")
        else:
            user_prompt = f"""
Purpose: {email_purpose}
Recipient: {to_whom}
Context: {context}
Tone: {style}

Write a clear, polite, professional email with a subject line and body.
"""
            system_prompt = (
                "You are an expert at writing professional emails that are polite, "
                "clear, and effective."
            )
            with st.spinner("Drafting email..."):
                output = call_openai(system_prompt, user_prompt, "Email Writer")

            if output:
                st.subheader("Email Draft")
                st.write(output)


# ---------- 5. Code Helper ----------
elif mode == "Code Helper":
    st.subheader("💻 Coding Helper")

    language = st.selectbox(
        "Language", ["Python", "JavaScript", "C++", "Java", "Other"]
    )
    help_type = st.selectbox(
        "What do you need?",
        ["Explain code", "Fix bug", "Write new function", "Optimize / Refactor"],
    )
    code_or_desc = st.text_area("Paste your code or describe the problem", height=200)

    if st.button("Get Coding Help"):
        if not code_or_desc.strip():
            st.warning("Please paste some code or describe your issue.")
        else:
            user_prompt = f"""
Language: {language}
Help type: {help_type}
Code or Description:
{code_or_desc}

Explain step by step, then give improved or fixed code if relevant.
Add comments to help a beginner understand.
"""
            system_prompt = (
                "You are a patient senior developer and teacher. You explain things "
                "clearly for beginners and provide clean, correct solutions."
            )
            with st.spinner("Thinking about your code..."):
                output = call_openai(system_prompt, user_prompt, "Code Helper")

            if output:
                st.subheader("Help & Solution")
                st.write(output)


# ---------- 6. Usage Analytics ----------
elif mode == "Usage Analytics":
    st.subheader("📊 Usage Analytics Dashboard")

    total = ss.analytics["total_requests"]
    free_req = ss.analytics["free_requests"]
    prem_req = ss.analytics["premium_requests"]
    per_mode = ss.analytics["per_mode"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests (this session)", total)
    col2.metric("Free Requests", free_req)
    col3.metric("Premium Requests", prem_req)

    st.write("---")
    st.markdown("#### Requests by Tool")
    if per_mode:
        for m, c in per_mode.items():
            st.write(f"- **{m}**: {c}")
    else:
        st.info("No requests yet. Start using the tools to see analytics here.")

    st.write("---")
    st.markdown("#### Session Info")
    st.write(f"First use at: `{ss.analytics['first_use_at']}`")
    if ss.premium_activated_at:
        st.write(f"Premium activated at: `{ss.premium_activated_at}`")
    else:
        st.write("Premium not activated in this session.")
