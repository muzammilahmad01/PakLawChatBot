import streamlit as st
from chatbotlogic import SimpleChatbot
import time

# Page configuration
st.set_page_config(
    page_title="Simple Q&A Chatbot",
    page_icon="🤖",
    layout="centered"
)

# Title and description
st.title("🤖 Simple Q&A Chatbot")
st.markdown("Ask me anything! I'm powered by an open-source language model via Groq.")

# Initialize chatbot in session state (this persists across reruns)
if 'chatbot' not in st.session_state:
    try:
        st.session_state.chatbot = SimpleChatbot()
        st.session_state.chat_ready = True
    except Exception as e:
        st.error(f"Error initializing chatbot: {str(e)}")
        st.error("Please check your Groq API key in the .env file")
        st.session_state.chat_ready = False

# Initialize chat history in session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Check if chatbot is ready
    if not st.session_state.get('chat_ready', False):
        st.error("Chatbot is not ready. Please check your configuration.")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # Show thinking indicator
                with st.spinner("Thinking..."):
                    response = st.session_state.chatbot.get_response(prompt)
                
                # Display response
                message_placeholder.markdown(response)
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                message_placeholder.markdown(error_message)
                response = error_message

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with additional info
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This is a simple Q&A chatbot built with:")
    st.write("- Streamlit for the UI")
    st.write("- LangChain for LLM integration")
    st.write("- Groq for fast inference")
    st.write("- Llama 3 open-source model")
    
    st.header("🔧 Controls")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    # Show current model info
    if st.session_state.get('chat_ready', False):
        st.header("🤖 Model Info")
        st.write(f"Model: {st.session_state.chatbot.model_name}")
        st.write(f"Temperature: {st.session_state.chatbot.temperature}")
        
    st.header("🔑 Setup")
    st.write("1. Get free Groq API key from groq.com")
    st.write("2. Add it to .env file")
    st.write("3. Restart the app")