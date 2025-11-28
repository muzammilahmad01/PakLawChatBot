import os
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()

try:
    from vector_store import VectorStoreManager
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️ RAG components not available. Running in basic mode.")

# Load API key and models from .env
groq_api_key = os.getenv("GROQ_API_KEY") 
primary_model = os.getenv("MODEL_PRIMARY", "llama-3.3-70b-versatile")
fallback_model = os.getenv("MODEL_FALLBACK", "llama-3.1-70b-versatile")

# System prompts
BASIC_SYSTEM_PROMPT = (
    "You are a helpful legal assistant chatbot specializing in Pakistani law. "
    "Provide clear, concise, and accurate information about Pakistani legal matters, "
    "procedures, and general legal concepts. Always include relevant sources and "
    "remind users to consult with qualified lawyers for specific legal advice."
)

RAG_SYSTEM_PROMPT = (
    "You are a helpful legal assistant chatbot specializing in Pakistani law. "
    "You have access to official Pakistani legal documents. Use the provided context to answer questions accurately. "
    "When referencing information from the context, cite the source document. "
    "If the context doesn't contain relevant information, say so clearly and provide general guidance if possible. "
    "Always remind users to consult with qualified lawyers for specific legal advice."
)

# Global vector store manager (loaded once)
_vector_store_manager: Optional[VectorStoreManager] = None


def load_vector_store() -> Optional[VectorStoreManager]:
    """Load vector store (singleton pattern)"""
    global _vector_store_manager
    
    if _vector_store_manager is not None:
        return _vector_store_manager
    
    if not RAG_AVAILABLE:
        return None
    
    try:
        # Try to load test vector store first
        manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_test",
            collection_name="pakistan_constitution"
        )
        
        if manager.load_vectorstore() is not None:
            _vector_store_manager = manager
            print("✓ RAG enabled: Loaded test vector store (Pakistan Constitution)")
            return _vector_store_manager
        
        # If test doesn't exist, try full dataset
        manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_full",
            collection_name="kpk_laws_full"
        )
        
        if manager.load_vectorstore() is not None:
            _vector_store_manager = manager
            print("✓ RAG enabled: Loaded full vector store (320 KPK Laws)")
            return _vector_store_manager
        
        print("⚠️ No vector store found. Run ingestion first. Using basic mode.")
        return None
        
    except Exception as e:
        print(f"⚠️ Error loading vector store: {str(e)}. Using basic mode.")
        return None


def get_rag_response(user_input: str, k: int = 3) -> Dict[str, any]:
    """
    Generate response using RAG (Retrieval Augmented Generation)
    
    Args:
        user_input: User's question
        k: Number of document chunks to retrieve
        
    Returns:
        Dict with 'response', 'sources', and 'context_used'
    """
    if not groq_api_key:
        return {
            "response": "⚠️ GROQ_API_KEY is missing. Please set it in your .env file.",
            "sources": [],
            "context_used": False
        }
    
    # Try to load vector store
    vector_store = load_vector_store()
    
    # If no RAG available, fall back to basic response
    if vector_store is None:
        return {
            "response": get_basic_response(user_input),
            "sources": [],
            "context_used": False
        }
    
    try:
        # Retrieve relevant documents
        retrieved_docs = vector_store.search(user_input, k=k)
        
        if not retrieved_docs:
            # No relevant docs found, use basic response
            return {
                "response": get_basic_response(user_input),
                "sources": [],
                "context_used": False
            }
        
        # Build context from retrieved documents
        context_parts = []
        sources = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            source_name = doc.metadata.get('source', 'Unknown')
            page_num = doc.metadata.get('page', 'N/A')
            
            context_parts.append(
                f"[Document {i}: {source_name}, Page {page_num}]\n{doc.page_content}\n"
            )
            
            sources.append({
                "source": source_name,
                "page": page_num,
                "content_preview": doc.page_content[:150] + "..."
            })
        
        context = "\n---\n".join(context_parts)
        
        # Create enhanced prompt with context
        enhanced_prompt = f"""Context from Pakistani legal documents:

{context}

---

User Question: {user_input}

Please answer the question based on the provided context. Cite the specific documents when referencing information."""
        
        # Generate response with context
        messages = [
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=enhanced_prompt)
        ]
        
        try:
            chat_primary = ChatGroq(
                model=primary_model,
                groq_api_key=groq_api_key,
                temperature=0.7
            )
            response = chat_primary.invoke(messages)
            
            return {
                "response": response.content,
                "sources": sources,
                "context_used": True
            }
            
        except Exception as e1:
            print(f"Primary model failed: {str(e1)}")
            try:
                chat_fallback = ChatGroq(
                    model=fallback_model,
                    groq_api_key=groq_api_key,
                    temperature=0.7
                )
                response = chat_fallback.invoke(messages)
                
                return {
                    "response": response.content,
                    "sources": sources,
                    "context_used": True
                }
                
            except Exception as e2:
                return {
                    "response": f"⚠️ Both models failed.\nPrimary: {str(e1)}\nFallback: {str(e2)}",
                    "sources": [],
                    "context_used": False
                }
        
    except Exception as e:
        print(f"RAG error: {str(e)}. Falling back to basic mode.")
        return {
            "response": get_basic_response(user_input),
            "sources": [],
            "context_used": False
        }


def get_basic_response(user_input: str) -> str:
    """
    Generate basic response without RAG (original functionality)
    """
    if not groq_api_key:
        return "⚠️ GROQ_API_KEY is missing. Please set it in your .env file."
    
    messages = [
        SystemMessage(content=BASIC_SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    try:
        chat_primary = ChatGroq(
            model=primary_model,
            groq_api_key=groq_api_key,
            temperature=0.7
        )
        response = chat_primary.invoke(messages)
        return response.content
        
    except Exception as e1:
        print(f"Primary model ({primary_model}) failed: {str(e1)}")
        try:
            chat_fallback = ChatGroq(
                model=fallback_model,
                groq_api_key=groq_api_key,
                temperature=0.7
            )
            response = chat_fallback.invoke(messages)
            return f"✓ (via Fallback) {response.content}"
            
        except Exception as e2:
            return f"⚠️ Both models failed.\nPrimary error: {str(e1)}\nFallback error: {str(e2)}"


# Main function - uses RAG by default
def get_chatbot_response(user_input: str, use_rag: bool = True) -> str:
    """
    Generate chatbot response (with or without RAG)
    
    Args:
        user_input: User's question
        use_rag: Whether to use RAG (default: True)
        
    Returns:
        String response (for backward compatibility)
    """
    if use_rag and RAG_AVAILABLE:
        result = get_rag_response(user_input)
        return result["response"]
    else:
        return get_basic_response(user_input)


# Backward compatibility
def get_response(user_input: str) -> str:
    return get_chatbot_response(user_input)