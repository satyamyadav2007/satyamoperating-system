import streamlit as st
import requests

# 1. Setup the Page
st.set_page_config(page_title="Agent OS", layout="centered")
st.title("🤖 Agent OS Interface")
st.caption("Powered by LangGraph & Llama 3")

# 2. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display Old Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle New User Input
if prompt := st.chat_input("Give your agent a command..."):
    # Show User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5. Send to Your Backend (The Brain)
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                # This hits your uvicorn server!
                response = requests.post(
                    "http://127.0.0.1:8000/chat", 
                    json={"message": prompt}
                )
                
                if response.status_code == 200:
                    ai_reply = response.json().get("response", "No response received.")
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                else:
                    st.error("Error: Could not connect to Agent Backend.")
            except Exception as e:
                st.error(f"Connection Failed: {e}")