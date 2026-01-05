import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

# Try to import RAG components
RAG_AVAILABLE = False
HYBRID_AVAILABLE = False

try:
    from vector_store import VectorStoreManager
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Vector store not available: {e}")

try:
    from retriever import HybridRetriever, build_bm25_from_vectorstore
    HYBRID_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Hybrid retriever not available: {e}. Using basic search.")

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

# Global instances (loaded once)
_vector_store_manager = None
_hybrid_retriever = None


def load_vector_store():
    """Load vector store (singleton pattern)"""
    global _vector_store_manager
    
    if _vector_store_manager is not None:
        return _vector_store_manager
    
    if not RAG_AVAILABLE:
        return None
    
    try:
        # Try to load FULL vector store first (priority)
        manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_full",
            collection_name="kpk_laws_full"
        )
        
        if manager.load_vectorstore() is not None:
            _vector_store_manager = manager
            print("✓ RAG enabled: Loaded full vector store (KPK Laws - 13k+ chunks)")
            return _vector_store_manager
        
        # Fall back to test vector store if full doesn't exist
        manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_test",
            collection_name="pakistan_constitution"
        )
        
        if manager.load_vectorstore() is not None:
            _vector_store_manager = manager
            print("✓ RAG enabled: Loaded test vector store (Pakistan Constitution)")
            return _vector_store_manager
        
        print("⚠️ No vector store found. Run ingestion first. Using basic mode.")
        return None
        
    except Exception as e:
        print(f"⚠️ Error loading vector store: {str(e)}. Using basic mode.")
        return None


def get_hybrid_retriever():
    """Get or create hybrid retriever (singleton pattern)"""
    global _hybrid_retriever
    
    if not HYBRID_AVAILABLE:
        return None
    
    if _hybrid_retriever is not None:
        return _hybrid_retriever
    
    vector_store = load_vector_store()
    if vector_store is None or vector_store.vectorstore is None:
        return None
    
    try:
        # Extract documents from vectorstore for BM25 indexing
        documents = build_bm25_from_vectorstore(vector_store.vectorstore)
        
        # Create hybrid retriever
        _hybrid_retriever = HybridRetriever(
            vectorstore=vector_store.vectorstore,
            documents=documents
        )
        print("✓ Hybrid retriever initialized (Semantic + BM25)")
        return _hybrid_retriever
        
    except Exception as e:
        print(f"⚠️ Could not initialize hybrid retriever: {e}")
        return None


def get_rag_response(user_input: str, k: int = 5) -> Dict[str, any]:
    """
    Generate response using RAG (Retrieval Augmented Generation)
    Uses Hybrid Search + Reranking if available
    
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
    
    vector_store = load_vector_store()
    
    # If no RAG available, fall back to basic response
    if vector_store is None:
        return {
            "response": get_basic_response(user_input),
            "sources": [],
            "context_used": False
        }
    
    try:
        # Try hybrid retriever first, fall back to basic search
        retriever = get_hybrid_retriever()
        
        if retriever is not None:
            # Hybrid search with reranking
            retrieved_docs = retriever.search(
                query=user_input,
                k=k,
                use_hybrid=True,
                use_rerank=True
            )
        else:
            # Fallback to basic semantic search
            retrieved_docs = vector_store.search(user_input, k=k)
        
        if not retrieved_docs:
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
                "preview": doc.page_content[:150] + "..."
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
    """Generate basic response without RAG"""
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


def get_chatbot_response(user_input: str, use_rag: bool = True) -> str:
    """Generate chatbot response (with or without RAG)"""
    if use_rag and RAG_AVAILABLE:
        result = get_rag_response(user_input)
        return result["response"]
    else:
        return get_basic_response(user_input)


# Backward compatibility
def get_response(user_input: str) -> str:
    return get_chatbot_response(user_input)