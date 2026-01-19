import streamlit as st
import requests

# 1. Setup the Page Configuration
st.set_page_config(page_title="Agent OS", layout="centered")
st.title("🤖 Agent OS Interface")
st.caption("Powered by LangGraph & Llama 3")

# --- CONFIGURATION ---
# Backend ka URL wahi hona chahiye jo main.py mein define hai
BACKEND_URL = "http://127.0.0.1:8000/spawn_agent"

# Sidebar for Settings (Optional but Professional)
with st.sidebar:
    st.header("⚙️ Settings")
    # Agar aapne auth lagaya hai to yahan key daalein, varna default chhod dein
    api_key = st.text_input("Enter API Key", value="12345", type="password")
    st.info("Ensure your Uvicorn server is running on port 8000")

# 2. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display Old Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle New User Input
if prompt := st.chat_input("Give your agent a command..."):
    # Display User Message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5. Send to Your Backend (The Brain)
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                # Payload creation
                payload = {
                    "user_id": "streamlit_user",
                    "task": prompt
                }
                
                # Headers for security
                headers = {
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                }

                # --- THE CONNECTION ---
                response = requests.post(BACKEND_URL, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Backend se jo bhi key aaye use yahan handle karein
                    # Agar backend {"status": "success", "trace": [...]} bhej raha hai:
                    ai_reply = str(data) # Safety ke liye pura JSON string banaya
                    
                    # Agar koi specific message field hai to use dikhayein:
                    if "response" in data:
                        ai_reply = data["response"]
                    elif "trace" in data:
                        ai_reply = f"✅ Task Completed. Trace: {data['trace'][-1]}"

                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
                elif response.status_code == 422:
                    st.error("Error 422: Data mismatch. Check if 'JobRequest' in main.py matches the payload.")
                
                elif response.status_code == 401:
                    st.error("Error 401: Unauthorized. Check your API Key.")
                
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Refused! Is 'uvicorn main:app --reload' running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")