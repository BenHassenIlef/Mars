import os
import streamlit as st
import requests
import json
import base64
from datetime import datetime
import time
import pytz
import pandas as pd
from streamlit_mic_recorder import mic_recorder
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Chat with Mars",
    page_icon="ss.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Constants
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
AVAILABLE_MODELS = {
    "Llama3-70B": "llama3-70b-8192",
    "Llama3-8B": "llama3-8b-8192",
    "Mixtral-8x7B": "mixtral-8x7b-32768"
}

# Function to convert image to base64
def get_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Apply fullscreen background with enhanced styling
background_image = get_base64("e.gif")
st.markdown(
    f"""
    <style>
    /* Main container */
    .stApp {{
        background-image: url("data:image/jpg;base64,{background_image}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* Chat message styling */
    .stChatMessage {{
        border-radius: 15px;
        margin-bottom: 15px;
        padding: 12px 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    
    /* User message styling */
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {{
        background-color: #4a8cff;
    }}
    
    /* Assistant message styling */
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {{
        background-color: #ff6b4a;
    }}
    
    /* Input box styling */
    .stTextInput > div > div > input {{
        background-color: rgba(255,255,255,0.8);
        border-radius: 20px;
        padding: 10px 15px;
    }}
    
    /* Button styling */
    .stButton > button {{
        border-radius: 20px;
        background-color: #4a8cff;
        color: white;
        font-weight: bold;
    }}
    
    /* Microphone button styling */
    .mic-button {{
        background-color: #ff4a4a !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm Mars, your advanced AI assistant. How can I help you today?"}
    ]
if "model" not in st.session_state:
    st.session_state.model = "llama3-70b-8192"
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = datetime.now(pytz.utc)
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# Function to transcribe audio
def transcribe_audio(audio_bytes):
    try:
        # Convert bytes to audio file
        audio = AudioSegment.from_file(BytesIO(audio_bytes))
        
        # Export as WAV (required by speech_recognition)
        wav_file = BytesIO()
        audio.export(wav_file, format="wav")
        wav_file.seek(0)
        
        # Use speech_recognition to transcribe
        r = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            return text
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None

# Sidebar for settings and additional features
with st.sidebar:
    st.image("ai.png", width=150)
    st.title("Mars Settings")
    
    # Model selection
    selected_model = st.selectbox(
        "Choose AI Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=0,
        key="model_select"
    )
    st.session_state.model = AVAILABLE_MODELS[selected_model]
    
    # Temperature control
    st.session_state.temperature = st.slider(
        "Creativity Level",
        min_value=0.1,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make responses more creative but less factual"
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a file for analysis",
        type=["txt", "pdf", "csv", "xlsx", "docx", "pptx"],
        accept_multiple_files=False
    )
    
    if uploaded_file:
        file_details = {
            "filename": uploaded_file.name,
            "filetype": uploaded_file.type,
            "filesize": uploaded_file.size
        }
        st.session_state.uploaded_files[uploaded_file.name] = {
            "file": uploaded_file,
            "details": file_details
        }
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    
    # Conversation statistics
    st.divider()
    st.subheader("Conversation Stats")
    duration = datetime.now(pytz.utc) - st.session_state.conversation_started
    st.write(f"⏱️ Duration: {duration.seconds // 60}m {duration.seconds % 60}s")
    st.write(f"💬 Messages: {len([m for m in st.session_state.messages if m['role'] == 'user'])}")
    
    # Clear conversation button
    if st.button("Clear Conversation"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Conversation cleared. How can I help you now?"}
        ]
        st.rerun()

# Main chat interface
st.title(" Mars AI Assistant")

# Display uploaded files
if st.session_state.uploaded_files:
    with st.expander("📁 Uploaded Files"):
        for filename, file_data in st.session_state.uploaded_files.items():
            col1, col2 = st.columns([3,1])
            col1.write(f"**{filename}** ({file_data['details']['filetype']})")
            if col2.button(f"Remove {filename}", key=f"remove_{filename}"):
                del st.session_state.uploaded_files[filename]
                st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to call Groq API with enhanced error handling
def call_groq_api(messages, model="llama3-70b-8192"):
    data = {
        "model": model,
        "messages": messages,
        "temperature": st.session_state.temperature,
        "max_tokens": 2048,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=30  # 30 seconds timeout
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        else:
            error_msg = f"API Error: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"
            return f"⚠️ I encountered an error: {error_msg}"
            
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please try again."
    except Exception as e:
        return f"⚠️ An unexpected error occurred: {str(e)}"

# Voice recording and text input
with st.container():
    col1, col2 = st.columns([5,1])
    
    with col1:
        user_prompt = st.chat_input("Message Mars...", key="chat_input")
    
    with col2:
        # Microphone button with custom styling
        audio_bytes = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=True,
            use_container_width=True,
            callback=None,
            args=(),
            kwargs={},
            key="recorder"
        )
        
        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes['bytes']
            st.toast("Audio recorded! Transcribing...", icon="🎤")
            
            # Transcribe the audio
            transcription = transcribe_audio(st.session_state.audio_bytes)
            if transcription:
                st.session_state.transcription = transcription
                st.rerun()

# Handle voice transcription
if "transcription" in st.session_state and st.session_state.transcription:
    user_prompt = st.session_state.transcription
    del st.session_state.transcription

# Handle user input (text or voice)
if user_prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    # Check if user uploaded a file and wants to analyze it
    file_context = ""
    if st.session_state.uploaded_files:
        for filename, file_data in st.session_state.uploaded_files.items():
            try:
                if file_data['details']['filetype'] == "text/plain":
                    content = str(file_data['file'].read(), "utf-8")
                    file_context += f"\n[User uploaded a text file '{filename}' with content: {content[:1000]}...]\n"
                elif file_data['details']['filetype'] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    df = pd.read_excel(file_data['file'])
                    file_context += f"\n[User uploaded an Excel file '{filename}' with {len(df)} rows. First 5 rows:\n{df.head().to_markdown()}\n]"
                elif file_data['details']['filetype'] == "text/csv":
                    df = pd.read_csv(file_data['file'])
                    file_context += f"\n[User uploaded a CSV file '{filename}' with {len(df)} rows. First 5 rows:\n{df.head().to_markdown()}\n]"
            except Exception as e:
                file_context += f"\n[Failed to process file '{filename}': {str(e)}]\n"
    
    # Prepare messages for API call
    api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
    
    # Add file context if available
    if file_context:
        api_messages[-1]["content"] += f"\n\nAdditional context from user's uploaded files:\n{file_context}"
    
    # Get assistant response with loading indicator
    with st.spinner("Mars is thinking..."):
        start_time = time.time()
        assistant_response = call_groq_api(api_messages, st.session_state.model)
        response_time = time.time() - start_time
    
    # Add response time to message
    assistant_response += f"\n\n⏱️ Response generated in {response_time:.2f} seconds"
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)


# Footer
st.markdown("---")
st.caption("Mars AI Assistant")