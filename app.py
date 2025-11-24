import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 5))
PREMIUM_ACCESS_CODE = os.getenv("PREMIUM_ACCESS_CODE", "")

if not OPENAI_API_KEY:
    st.set_page_config(page_title="SuperBrain AI", layout="wide")
    st.error(
        "No OpenAI API key found.\n\n"
        "Set **OPENAI_API_KEY** in your `.env` (local) or **Secrets** (Streamlit Cloud)."
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------
# Page configuration
# -------------------------
st.set_page_config(page_title="SuperBrain AI", layout="wide")

# -------------------------
# Session state init
# -------------------------
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "chat_history" not in st.session_state:
    # list[dict]: {"role": "user"/"assistant", "content": "..."}
    st.session_state.chat_history = []

if "first_used_at" not in st.session_state:
    st.session_state.first_used_at = datetime.utcnow().isoformat()

if "show_premium_popup" not in st.session_state:
    st.session_state.show_premium_popup = False

if "mode" not in st.session_state:
    st.session_state.mode = "General Chat"

# -------------------------
# Helper functions
# -------------------------
APP_NAME = "SuperBrain AI"


def can_use_ai() -> bool:
    """Check if the user is allowed to make another request."""
    if st.session_state.is_premium:
        return True

    if st.session_state.request_count >= FREE_DAILY_LIMIT:
        st.warning(
            f"⚠️ You reached the free limit of **{FREE_DAILY_LIMIT}** requests "
            "for this session.\n\nUpgrade to **Premium** for unlimited access."
        )
        return False
    return True


def register_request() -> None:
    """Increment request counter for non-premium users."""
    if not st.session_state.is_premium:
        st.session_state.request_count += 1


def call_openai(system_prompt: str, user_prompt: str) -> str | None:
    """Wrapper around OpenAI chat.completions."""
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


def add_chat_message(role: str, content: str) -> None:
    st.session_state.chat_history.append({"role": role, "content": content})


# -------------------------
# Global styles (chat bubbles, etc.)
# -------------------------
st.markdown(
    """
    <style>
        /* Center top logo */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-top: 0.5rem;
            margin-bottom: 0.3rem;
        }

        /* Premium badge */
        .premium-badge {
            text-align: center;
            padding: 6px 16px;
            border-radius: 999px;
            display: inline-block;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .premium-badge-free {
            background: linear-gradient(90deg, #f97316, #facc15);
            color: #111827;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .premium-badge-pro {
            background: linear-gradient(90deg, #4f46e5, #9333ea);
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        /* Chat bubbles */
        .chat-bubble-user {
            background: #2563eb;
            color: white;
            padding: 0.7rem 0.9rem;
            border-radius: 16px 16px 4px 16px;
            margin-bottom: 0.4rem;
            max-width: 80%;
            margin-left: auto;
            font-size: 0.95rem;
        }
        .chat-bubble-ai {
            background: #f3f4f6;
            color: #111827;
            padding: 0.7rem 0.9rem;
            border-radius: 16px 16px 16px 4px;
            margin-bottom: 0.4rem;
            max-width: 80%;
            margin-right: auto;
            font-size: 0.95rem;
        }
        .chat-label {
            font-size: 0.75rem;
            color: #6b7280;
            margin-bottom: 0.1rem;
        }
        .chat-label-user {
            text-align: right;
        }
        .chat-label-ai {
            text-align: left;
        }

        /* Premium popup card */
        .premium-popup {
            border-radius: 18px;
            padding: 1.2rem 1.4rem;
            background: linear-gradient(135deg, #0f172a, #111827);
            color: #e5e7eb;
            box-shadow: 0 18px 40px rgba(15,23,42,0.7);
            border: 1px solid #4f46e5;
        }

        /* Analytics cards */
        .metric-card {
            padding: 0.9rem 1rem;
            border-radius: 14px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Sidebar (theme + modes + premium)
# -------------------------
st.sidebar.title(APP_NAME)

theme_choice = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
if theme_choice == "Dark":
    st.markdown(
        """
        <style>
        .stApp { background-color: #020617; color: #e5e7eb; }
        .metric-card { background: #020617; border-color: #1f2937; }
        .chat-bubble-ai { background: #111827; color: #e5e7eb; }
        </style>
        """,
        unsafe_allow_html=True,
    )

mode = st.sidebar.selectbox(
    "Choose AI Tool",
    [
        "General Chat",
        "Resume & Cover Letter",
        "Blog / Social Post Writer",
        "Email Writer",
        "Code Helper",
        "Usage Analytics",
    ],
)
st.session_state.mode = mode

st.sidebar.subheader("Usage")
remaining = (
    "Unlimited" if st.session_state.is_premium else max(FREE_DAILY_LIMIT - st.session_state.request_count, 0)
)
st.sidebar.write(f"Requests used: **{st.session_state.request_count}**")
st.sidebar.write(f"Requests remaining: **{remaining}**")

if not st.session_state.is_premium:
    st.sidebar.progress(
        min(st.session_state.request_count / max(FREE_DAILY_LIMIT, 1), 1.0)
    )

st.sidebar.markdown("---")

# Premium unlock by code
st.sidebar.subheader("🔑 Have a Premium Code?")
code_input = st.sidebar.text_input("Enter access code", type="password")
if st.sidebar.button("Unlock Premium"):
    if PREMIUM_ACCESS_CODE and code_input == PREMIUM_ACCESS_CODE:
        st.session_state.is_premium = True
        st.session_state.request_count = 0
        st.success("🎉 Premium unlocked – enjoy unlimited usage!")
    else:
        st.error("❌ Invalid or missing premium code.")

# Show upgrade info only if not premium
if not st.session_state.is_premium:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💳 Upgrade to Premium")
    st.sidebar.markdown(
        "[Pay ₹299 on Razorpay](https://rzp.io/rzp/HuxrI9w)"
    )
    st.sidebar.caption(
        "After payment, your **SuperBrain AI Premium Code** will be sent to you.\n"
        "Enter it above to unlock unlimited access."
    )

# Button to open premium popup
if not st.session_state.is_premium:
    if st.sidebar.button("View Premium Benefits"):
        st.session_state.show_premium_popup = True
else:
    st.sidebar.success("You are a Premium user. 🚀")

# -------------------------
# Top: Logo + Title + Badge
# -------------------------
# Resolve logo path safely
logo_path = "superbrain_logo.png"
if not os.path.exists(logo_path):
    # backup name used earlier
    if os.path.exists("SuperBrain.png"):
        logo_path = "SuperBrain.png"
    else:
        logo_path = None

if logo_path:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(logo_path, width=150)
    st.markdown("</div>", unsafe_allow_html=True)

# Badge (no "Free" watermark for premium)
st.markdown(
    '<div style="text-align:center;">',
    unsafe_allow_html=True,
)
if st.session_state.is_premium:
    st.markdown(
        '<span class="premium-badge premium-badge-pro">✨ Premium User — Unlimited Access</span>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<span class="premium-badge premium-badge-free">⚡ Free User — Limited Access</span>',
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

st.title(APP_NAME)
st.caption("Your multi-skill AI assistant powered by OpenAI + Streamlit.")

# -------------------------
# Premium Popup (simple modal-like card)
# -------------------------
if st.session_state.show_premium_popup and not st.session_state.is_premium:
    with st.container():
        st.markdown('<div class="premium-popup">', unsafe_allow_html=True)
        cols = st.columns([3, 1])
        with cols[0]:
            st.subheader("🚀 SuperBrain AI Premium")
            st.write(
                "- Unlimited AI requests per session\n"
                "- Faster responses for heavy prompts\n"
                "- Priority for new tools & features\n"
                "- No free-tier usage limits or banners"
            )
            st.write("After you pay on Razorpay, you'll receive a **Premium Access Code** by email.")
        with cols[1]:
            st.markdown("**Price**")
            st.markdown("### ₹299 / month")
            st.markdown(
                "[Upgrade via Razorpay](https://rzp.io/rzp/HuxrI9w)",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Close Premium Details"):
            st.session_state.show_premium_popup = False

st.write("---")

# -------------------------
# MAIN MODES
# -------------------------

# 1) GENERAL CHAT
if mode == "General Chat":
    st.subheader("💬 Chat with AI")

    user_message = st.text_area("Type your message:", key="general_chat_box")
    send_clicked = st.button("Send")

    if send_clicked and user_message.strip():
        add_chat_message("user", user_message)

        # Build messages with history
        messages = [
            {"role": "system", "content": "You are a helpful, friendly AI assistant named SuperBrain."}
        ]
        for m in st.session_state.chat_history:
            messages.append({"role": m["role"], "content": m["content"]})

        if can_use_ai():
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )
                reply = res.choices[0].message.content
                register_request()
                add_chat_message("assistant", reply)
            except Exception as e:
                st.error(f"Error talking to model: {e}")

    # Chat bubble display
    st.markdown("#### Conversation")
    if not st.session_state.chat_history:
        st.info("Start chatting by typing a message above.")
    else:
        for m in st.session_state.chat_history:
            role = m["role"]
            content = m["content"]
            if role == "user":
                st.markdown(
                    '<div class="chat-label chat-label-user">You</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="chat-bubble-user">{content}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="chat-label chat-label-ai">SuperBrain AI</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="chat-bubble-ai">{content}</div>',
                    unsafe_allow_html=True,
                )

# 2) RESUME & COVER LETTER
elif mode == "Resume & Cover Letter":
    st.subheader("📄 Resume & Cover Letter Assistant")

    name = st.text_input("Your Name")
    role = st.text_input("Target Role (e.g., Python Developer)")
    skills = st.text_area("Skills (comma separated)")
    projects = st.text_area("Projects (briefly describe)")
    experience = st.text_area("Internships / Experience")
    extras = st.text_area("Extra info (certificates, hackathons, achievements)")
    tone = st.selectbox(
        "Tone",
        ["Professional", "Friendly professional", "Very formal"],
    )

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

Do not invent fake experience. Be honest but positive.
"""
            output = call_openai(
                "You are an expert HR and resume writer helping job seekers.", user_prompt
            )
            if output:
                st.subheader("Generated Content")
                st.write(output)

# 3) BLOG / SOCIAL POST WRITER
elif mode == "Blog / Social Post Writer":
    st.subheader("✍️ Blog & Social Media Content Writer")

    content_type = st.selectbox(
        "Content Type",
        ["Blog Post", "LinkedIn Post", "Instagram Caption", "Twitter / X Thread"],
    )
    topic = st.text_input("Topic / Title")
    audience = st.text_input("Target Audience (e.g., freshers, small business owners)")
    length = st.selectbox("Length", ["Short", "Medium", "Long"])
    extras = st.text_area("Extra instructions (tone, call to action, etc.)")

    if st.button("Generate Content"):
        if not topic.strip():
            st.warning("Please provide a topic or title.")
        else:
            prompt = f"""
Content type: {content_type}
Topic: {topic}
Target audience: {audience}
Length: {length}
Extra instructions: {extras}

Write high-quality, original content that is helpful and engaging.
Avoid generic fluff; provide structure, value, and a clear message.
"""
            output = call_openai(
                "You are an expert content writer and social media marketer.", prompt
            )
            if output:
                st.subheader("Generated Content")
                st.write(output)

# 4) EMAIL WRITER
elif mode == "Email Writer":
    st.subheader("📧 Professional Email Writer")

    email_purpose = st.selectbox(
        "Email Purpose",
        [
            "Job Application",
            "Follow-up after Interview",
            "Cold Email to Client",
            "Networking / Connection Request",
            "General Professional Email",
        ],
    )
    to_whom = st.text_input("Recipient (e.g., HR, Manager, Client)")
    context = st.text_area("Context or Details (what is this email about?)")
    style = st.selectbox("Tone", ["Formal", "Semi-formal", "Friendly professional"])

    if st.button("Generate Email"):
        if not context.strip():
            st.warning("Please provide some context so the email is accurate.")
        else:
            prompt = f"""
Purpose: {email_purpose}
Recipient: {to_whom}
Context: {context}
Tone: {style}

Write a clear, polite, professional email.
Include both a subject line and the email body.
"""
            output = call_openai(
                "You are an expert at writing professional, polite emails.", prompt
            )
            if output:
                st.subheader("Email Draft")
                st.write(output)

# 5) CODE HELPER
elif mode == "Code Helper":
    st.subheader("💻 Code Helper")

    language = st.selectbox(
        "Language",
        ["Python", "JavaScript", "C++", "Java", "Other"],
    )
    help_type = st.selectbox(
        "What do you need?",
        ["Explain code", "Fix bug", "Write new function", "Optimize / Refactor"],
    )
    code_or_desc = st.text_area(
        "Paste your code or describe the problem", height=200
    )

    if st.button("Get Coding Help"):
        if not code_or_desc.strip():
            st.warning("Please paste some code or description.")
        else:
            prompt = f"""
Language: {language}
Help type: {help_type}
Code or description:
{code_or_desc}

Explain step by step, then give the improved or fixed code if relevant.
Add comments in the code to help a beginner understand.
"""
            output = call_openai(
                "You are a patient senior developer and teacher.",
                prompt,
            )
            if output:
                st.subheader("Help & Solution")
                st.write(output)

# 6) USAGE ANALYTICS
elif mode == "Usage Analytics":
    st.subheader("📊 Session Analytics")

    total_requests = st.session_state.request_count
    first_used = st.session_state.first_used_at

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Requests This Session", total_requests)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            "Plan",
            "Premium" if st.session_state.is_premium else "Free",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.write("First used at (UTC):")
        st.write(first_used.split(".")[0].replace("T", " "))
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("---")
    st.write(
        "This analytics page currently shows **session-level** statistics. "
        "You can extend it later to log data to a database (e.g., Supabase, Postgres) "
        "for long-term tracking."
    )
