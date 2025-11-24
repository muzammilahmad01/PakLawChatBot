import streamlit as st
from chatbotlogic import get_chatbot_response

# Page configuration
st.set_page_config(
    page_title="PakLaw ChatBot", 
    layout="wide",
    page_icon="⚖️"
)

# Header
st.title("⚖️ PakLaw ChatBot")
st.markdown("---")

# Description
st.markdown("""
### Welcome to PakLaw ChatBot! 
Ask me anything about Pakistani law, legal procedures, or general legal questions.
I'm here to help with clear and concise answers.
""")

# Initialize chat history in session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    # Add a welcome message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello! I'm your PakLaw ChatBot. How can I help you with legal questions today?"
    })

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about Pakistani law or legal procedures..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Analyzing your question..."):
            try:
                response = get_chatbot_response(prompt)
                if not response or response.strip() == "":
                    response = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            except Exception as e:
                response = f"⚠️ Error occurred: {str(e)}\n\nPlease check your API configuration and try again."
                st.error(f"Error details: {str(e)}")
        
        message_placeholder.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with additional info
with st.sidebar:
    st.header("ℹ️ About PakLaw ChatBot")
    st.write("""
    This chatbot specializes in Pakistani legal information and is built with:
    
    This chatbot specializes in Pakistani legal information and is built with:
- **Streamlit** for the user interface
- **LangChain** for LLM integration  
- **Gemini (Google AI)** for intelligent inference
""")

    st.header("🔧 Controls")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        # Add welcome message back
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm your PakLaw ChatBot. How can I help you with legal questions today?"
        })
        st.rerun()

    st.header("💡 Tips")
    st.write("""
    - Ask specific questions about Pakistani law
    - Include context for better answers
    - Be clear about the legal area you're asking about
    - Remember: This is for informational purposes only
    """)
    
    st.header("⚠️ Disclaimer")
    st.write("""
    This chatbot provides general legal information only. 
    Always consult with a qualified lawyer for specific legal advice.
    """)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>PakLaw ChatBot - Your AI Legal Assistant</p>", 
    unsafe_allow_html=True
)