import streamlit as st
import requests
import json

st.title("Chatbot")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input field for user query
if prompt := st.chat_input("How can I assist you today?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send query to FastAPI backend
    try:
        response = requests.post("http://localhost:5000/query", json={"text": prompt})
        response_data = response.json()
        bot_response = response_data["response"]
    except:
        bot_response = "Error: Could not process your request."

    # Display bot response
    with st.chat_message("assistant"):
        st.markdown(bot_response)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})