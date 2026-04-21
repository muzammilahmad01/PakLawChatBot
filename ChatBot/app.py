# import streamlit as st
# from chatbotlogic import get_rag_response, get_basic_response

# # Page configuration
# st.set_page_config(
#     page_title="PakLaw ChatBot", 
#     layout="wide",
#     page_icon="⚖️"
# )

# # Header
# st.title("⚖️ PakLaw ChatBot")
# st.markdown("---")

# # Description
# st.markdown("""
# ### Welcome to PakLaw ChatBot! 
# Ask me anything about Pakistani law, legal procedures, or general legal questions.
# I'm here to help with clear and concise answers.
# """)

# # Initialize session state
# if 'messages' not in st.session_state:
#     st.session_state.messages = []
#     # Add a welcome message
#     st.session_state.messages.append({
#         "role": "assistant", 
#         "content": "Hello! I'm your PakLaw ChatBot. How can I help you with legal questions today?",
#         "sources": None
#     })

# # Initialize RAG toggle (default: enabled)
# if 'use_rag' not in st.session_state:
#     st.session_state.use_rag = True

# # Display chat history
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
        
#         # Display sources if available (for assistant messages with RAG)
#         if message["role"] == "assistant" and message.get("sources"):
#             with st.expander("📚 Sources Used", expanded=False):
#                 for i, source in enumerate(message["sources"], 1):
#                     st.markdown(f"**Source {i}:** {source['source']} (Page {source['page']})")
#                     st.caption(f"Preview: {source['content_preview']}")
#                     if i < len(message["sources"]):
#                         st.markdown("---")

# # Chat input
# if prompt := st.chat_input("Ask me about Pakistani law or legal procedures..."):
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt, "sources": None})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Get bot response
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         sources_placeholder = st.empty()
        
#         with st.spinner("🔍 Searching legal documents and analyzing your question..."):
#             try:
#                 # Use RAG if enabled, otherwise use basic mode
#                 if st.session_state.use_rag:
#                     result = get_rag_response(prompt, k=3)
#                     response = result["response"]
#                     sources = result["sources"]
#                     context_used = result["context_used"]
#                 else:
#                     response = get_basic_response(prompt)
#                     sources = []
#                     context_used = False
                
#                 if not response or response.strip() == "":
#                     response = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
#                     sources = []
#                     context_used = False
                    
#             except Exception as e:
#                 response = f"⚠️ Error occurred: {str(e)}\\n\\nPlease check your API configuration and try again."
#                 sources = []
#                 context_used = False
#                 st.error(f"Error details: {str(e)}")
        
#         # Display the response
#         message_placeholder.markdown(response)
        
#         # Display sources if RAG was used
#         if sources and context_used:
#             with sources_placeholder.container():
#                 with st.expander("📚 Sources Used", expanded=False):
#                     st.caption(f"✓ Answer based on {len(sources)} document(s)")
#                     for i, source in enumerate(sources, 1):
#                         st.markdown(f"**Source {i}:** {source['source']} (Page {source['page']})")
#                         st.caption(f"Preview: {source['content_preview']}")
#                         if i < len(sources):
#                             st.markdown("---")
#         elif st.session_state.use_rag and not context_used:
#             with sources_placeholder.container():
#                 st.info("ℹ️ No relevant documents found. Answer based on general knowledge.")

#     # Add assistant response to chat history
#     st.session_state.messages.append({
#         "role": "assistant", 
#         "content": response,
#         "sources": sources if context_used else None
#     })

# # Sidebar with additional info
# with st.sidebar:
#     st.header("ℹ️ About PakLaw ChatBot")
#     st.write("""
#     This chatbot specializes in Pakistani legal information and is built with:
    
# - **Streamlit** for the user interface
# - **LangChain** for LLM integration  
# - **Groq Cloud** for fast AI inference
# - **RAG** for document-based answers
# """)

#     st.markdown("---")
    
#     # RAG Toggle
#     st.header("🔧 Settings")
#     use_rag = st.checkbox(
#         "Enable RAG (Document Search)", 
#         value=st.session_state.use_rag,
#         help="When enabled, the chatbot will search Pakistani law documents to answer your questions."
#     )
#     st.session_state.use_rag = use_rag
    
#     if st.session_state.use_rag:
#         st.success("✓ RAG Enabled - Using Pakistan's Constitution")
#     else:
#         st.warning("⚠️ RAG Disabled - Using general knowledge only")
    
#     st.markdown("---")

#     st.header("🔧 Controls")
#     if st.button("🗑️ Clear Chat History"):
#         st.session_state.messages = []
#         # Add welcome message back
#         st.session_state.messages.append({
#             "role": "assistant", 
#             "content": "Hello! I'm your PakLaw ChatBot. How can I help you with legal questions today?",
#             "sources": None
#         })
#         st.rerun()

#     st.header("💡 Tips")
#     st.write("""
#     - Ask specific questions about Pakistani law
#     - Include context for better answers
#     - Be clear about the legal area you're asking about
#     - Remember: This is for informational purposes only
#     """)
    
#     st.header("⚠️ Disclaimer")
#     st.write("""
#     This chatbot provides general legal information only. 
#     Always consult with a qualified lawyer for specific legal advice.
#     """)

# # Footer
# st.markdown("---")
# st.markdown(
#     "<p style='text-align: center; color: gray;'>PakLaw ChatBot - Your AI Legal Assistant</p>", 
#     unsafe_allow_html=True
# )