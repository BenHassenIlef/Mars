import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
import pytz
import pandas as pd
import base64
from PIL import Image
import time

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Mars AI Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with input bar at bottom
def inject_custom_css():
    st.markdown(f"""
    <style>
        /* Main app styling */
        .stApp {{
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }}
        
        /* Chat container */
        .main .block-container {{
            flex: 1;
            padding-bottom: 100px; /* Space for input bar */
        }}
        
        /* Fixed input bar at bottom */
        .stTextInput {{
            position: fixed;
            bottom: 20px;
            left: 2rem;
            right: 2rem;
            z-index: 999;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 15px;
            border-radius: 20px;
            width: calc(100% - 4rem);
            max-width: 1200px;
            margin: 0 auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        /* Adjust chat messages to not hide behind input */
        .stChatMessage {{
            margin-bottom: 80px;
        }}
        
        /* Other existing styles */
        .stChatMessage {{
            border-radius: 18px;
            padding: 16px 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {{
            background: linear-gradient(135deg, #667eea, #764ba2);
        }}
        
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {{
            background: linear-gradient(135deg, #ff758c, #ff7eb3);
        }}
        
        .stTextInput > div > div > input {{
            background-color: rgba(255,255,255,0.15);
            color: white;
            border-radius: 15px;
            padding: 12px 18px;
            border: none;
            font-size: 16px;
        }}
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Set up Google Gemini-Pro AI model
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize session state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = genai.GenerativeModel(model_name="gemini-1.0-pro").start_chat(history=[])
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = datetime.now(pytz.utc)

# Sidebar content
with st.sidebar:
    st.title("Mars AI Settings")
    # ... [rest of your sidebar content] ...

# Main chat area
st.title("🤖 Mars AI Assistant")

# Display chat history
for message in st.session_state.chat_session.history:
    with st.chat_message("assistant" if message.role == "model" else "user"):
        st.markdown(message.parts[0].text)

# Quick actions
col1, col2, col3 = st.columns(3)
if col1.button("Summarize"):
    st.session_state.chat_session.send_message("Summarize our conversation")
    st.rerun()
if col2.button("Suggest Ideas"):
    st.session_state.chat_session.send_message("Suggest 3 creative ideas")
    st.rerun()
if col3.button("Explain Simply"):
    st.session_state.chat_session.send_message("Explain the last concept simply")
    st.rerun()

# Input bar (will appear at bottom due to CSS)
user_input = st.chat_input("Message Mars...")

if user_input:
    # Add user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_session.send_message(user_input)
            st.markdown(response.text)