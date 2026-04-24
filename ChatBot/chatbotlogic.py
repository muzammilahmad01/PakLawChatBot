import os
import time
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
fallback_model = os.getenv("MODEL_FALLBACK", "openai/gpt-oss-20b")

# System prompts
BASIC_SYSTEM_PROMPT = """You are PakLawChatBot, a knowledgeable Pakistani legal assistant. Your goal is to help users understand Pakistani law clearly and thoroughly.

RESPONSE STYLE:
- Start with a clear, direct answer to the question (2-3 sentences)
- Then provide a well-structured explanation with relevant details
- Use **bold** for important legal terms, article numbers, and section references (e.g., **Article 25**, **Section 302 PPC**)
- Use numbered lists when explaining multiple points, with a brief explanation for each
- Include relevant legal references (Act names, Article/Section numbers) wherever possible
- Use simple, easy-to-understand language — avoid unnecessary legal jargon
- If a legal term must be used, briefly explain what it means in parentheses
- Aim for a balanced response: thorough enough to be helpful, but not overwhelming
- Structure longer responses with clear sections using headings where appropriate

IMPORTANT:
- Always mention the specific law, act, or article that applies to the question
- If there are practical implications (e.g., penalties, procedures, rights), include them
- End with: "⚖️ *This is general legal information. Consult a qualified lawyer for advice specific to your situation.*"
"""

RAG_SYSTEM_PROMPT = """You are PakLawChatBot, a knowledgeable Pakistani legal assistant with access to legal documents and statutes.

RESPONSE STYLE:
- Start with a clear, direct answer to the question (2-3 sentences summarizing the key point)
- Then provide a detailed explanation using the context from the legal documents provided
- DO NOT say "the documents don't contain", "based on the provided context", or "according to the documents"
- Just answer naturally as if you already know the law — the context is your knowledge
- Use **bold** for important legal terms, article numbers, and section references
- Use numbered lists when explaining multiple points:
  1. **Legal Term / Article / Right** — Clear explanation of what it means and how it applies
  2. **Next Point** — Continue with relevant details
- Include the specific law name, act, section, or article number whenever the context provides it
- Explain legal concepts in plain language so a non-lawyer can understand
- If the law mentions penalties, punishments, procedures, or time limits — include them
- Structure longer responses with clear flow: What is it → How it works → What it means for you

IMPORTANT:
- Cite specific sections and articles from the context (e.g., "Under **Section 379 of the Pakistan Penal Code**...")
- If the question involves rights, explain both the right AND any exceptions or conditions
- If the question involves a procedure, explain the steps clearly
- End with: "⚖️ *This is general legal information. Consult a qualified lawyer for advice specific to your situation.*"
"""

# Category metadata: user-facing name, topic scope, and suggested category key
CATEGORY_INFO = {
    "criminal": {
        "name": "Criminal Laws",
        "scope": "Pakistan Penal Code (PPC), Criminal Procedure Code (CrPC), offences, punishments, bail, FIR, arrests, trials",
        "off_topic_examples": "marriage, divorce, property transfer, cyber crimes, labour rights, constitutional rights"
    },
    "Family": {
        "name": "Family Laws",
        "scope": "Muslim Family Laws Ordinance (MFLO), marriage, nikah, divorce, talaq, khula, child custody, maintenance, inheritance, guardianship",
        "off_topic_examples": "criminal offences, property registration, cyber crimes, labour wages, constitutional petitions"
    },
    "Property": {
        "name": "Property & Land Laws",
        "scope": "Transfer of Property Act, land revenue, mutation, property registration, landlord-tenant, inheritance of property",
        "off_topic_examples": "criminal law, family courts, cyber crimes, employment rights, constitutional rights"
    },
    "cyber": {
        "name": "Cyber Crime Laws",
        "scope": "PECA 2016, PTA regulations, online crimes, electronic fraud, data protection, social media, digital offences",
        "off_topic_examples": "physical crimes, family matters, property disputes, labour rights, constitutional law"
    },
    "labour": {
        "name": "Labour Laws",
        "scope": "Employment contracts, wages, termination, workers rights, workplace safety, factories act, social security, EOBI",
        "off_topic_examples": "criminal offences, family law, property law, cyber crimes, constitutional petitions"
    },
    "constitutional": {
        "name": "Constitutional Rights",
        "scope": "Constitution of Pakistan, fundamental rights (Articles 8-28), writ petitions, Supreme Court, High Court jurisdiction",
        "off_topic_examples": "specific criminal procedures, family court procedures, property registration, employment disputes"
    },
    "general": {
        "name": "General Legal Query",
        "scope": "All areas of Pakistani law — criminal, family, property, cyber, labour, constitutional, and more",
        "off_topic_examples": None  # General handles everything
    }
}


def build_rag_system_prompt(category: str = None) -> str:
    """
    Build a category-aware RAG system prompt.
    Injects the active category's scope so the model can:
    1. Focus retrieval context on relevant law
    2. Detect off-topic questions and politely redirect the user
    """
    cat_info = CATEGORY_INFO.get(category) if category else None

    # Category-specific instructions block
    if cat_info and cat_info.get("off_topic_examples"):
        category_block = f"""
ACTIVE CATEGORY: {cat_info['name']}
This category covers: {cat_info['scope']}

OFF-TOPIC QUESTION HANDLING:
If the user's question is clearly outside this category (e.g., about {cat_info['off_topic_examples']}),
you MUST:
1. Still provide a brief, helpful answer using your general knowledge of Pakistani law
2. At the END of your response, add a clearly separated note like this:

---
📂 **Category Notice:** Your question appears to be about [detected topic], which is better covered in a
different category. For a more detailed and accurate answer, please go back to the Dashboard and select
the **[suggest the most relevant category name]** category. If you're unsure which category applies,
use the **General Legal Query** category — it covers all areas of Pakistani law.

IMPORTANT: Only add this notice when the question is genuinely off-topic for this category.
Do NOT add it for questions that have any connection to {cat_info['name']}.
"""
    elif cat_info:
        # General category — no off-topic notice needed
        category_block = f"""
ACTIVE CATEGORY: {cat_info['name']}
This category covers: {cat_info['scope']}
Answer all questions thoroughly — this is the general category and covers all areas of Pakistani law.
"""
    else:
        category_block = ""

    return f"""You are PakLawChatBot, a knowledgeable Pakistani legal assistant with access to legal documents and statutes.
{category_block}
RESPONSE STYLE:
- Start with a clear, direct answer to the question (2-3 sentences summarizing the key point)
- Then provide a detailed explanation using the context from the legal documents provided
- DO NOT say "the documents don't contain", "based on the provided context", or "according to the documents"
- Just answer naturally as if you already know the law — the context is your knowledge
- Use **bold** for important legal terms, article numbers, and section references
- Use numbered lists when explaining multiple points:
  1. **Legal Term / Article / Right** — Clear explanation of what it means and how it applies
  2. **Next Point** — Continue with relevant details
- Include the specific law name, act, section, or article number whenever the context provides it
- Explain legal concepts in plain language so a non-lawyer can understand
- If the law mentions penalties, punishments, procedures, or time limits — include them
- Structure longer responses with clear flow: What is it → How it works → What it means for you

CRITICAL - DO NOT REFERENCE INTERNAL DOCUMENTS:
- NEVER mention "Document 1", "Document 2", etc. in your response
- NEVER mention PDF file names (e.g., "Pakistan's Constituion.pdf") in your response
- NEVER include page numbers like "Page 1", "Page 42" in your response
- NEVER say phrases like "according to Document 1" or "as stated in Document 3"
- Instead, cite the LEGAL SOURCE directly: use the Act name, Article number, or Section number
  Example: Say "Under Article 25 of the Constitution" NOT "according to Document 1: Pakistan's Constituion.pdf, Page 5"

IMPORTANT:
- Cite specific sections and articles by their legal names (e.g., "Section 302 PPC", "Article 25")
- If the question involves rights, explain both the right AND any exceptions or conditions
- If the question involves a procedure, explain the steps clearly
- End with: "⚖️ *This is general legal information. Consult a qualified lawyer for advice specific to your situation.*"
"""

# Global instances (loaded once)
_vector_store_manager = None
_hybrid_retriever = None

# Cached LLM clients (reused across requests to avoid connection setup overhead)
_llm_primary = None
_llm_fallback = None


def _get_llm_primary():
    """Get or create cached primary LLM client"""
    global _llm_primary
    if _llm_primary is None and groq_api_key:
        _llm_primary = ChatGroq(
            model=primary_model,
            groq_api_key=groq_api_key,
            temperature=0.7
        )
        print(f"[OK] Primary LLM client cached: {primary_model}")
    return _llm_primary


def _get_llm_fallback():
    """Get or create cached fallback LLM client"""
    global _llm_fallback
    if _llm_fallback is None and groq_api_key:
        _llm_fallback = ChatGroq(
            model=fallback_model,
            groq_api_key=groq_api_key,
            temperature=0.7
        )
        print(f"[OK] Fallback LLM client cached: {fallback_model}")
    return _llm_fallback


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
            collection_name="paklaw_docs"
        )
        
        if manager.load_vectorstore() is not None:
            _vector_store_manager = manager
            print("✓ RAG enabled: Loaded full vector store (PakLaw Docs)")
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


def get_rag_response(user_input: str, k: int = 5, category_filter: dict = None, category: str = None) -> Dict[str, any]:
    """
    Generate response using RAG (Retrieval Augmented Generation)
    Uses Hybrid Search + Reranking if available

    Args:
        user_input: User's question
        k: Number of document chunks to retrieve
        category_filter: Optional dict for filtering by category (e.g., {"department": "Criminal_Laws"})
        category: The UI category key (e.g., "criminal", "Family") for category-aware prompting

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
    
    # If no RAG available, inform user (NO fallback to general knowledge)
    if vector_store is None:
        return {
            "response": "⚠️ The legal document database is not available. Please ensure the vector store is loaded.",
            "sources": [],
            "context_used": False
        }
    
    try:
        total_start = time.time()
        
        # ── Step 1: Retrieval ──
        retrieval_start = time.time()
        retriever = get_hybrid_retriever()
        
        if retriever is not None:
            # Hybrid search with reranking and optional category filter
            retrieved_docs = retriever.search(
                query=user_input,
                k=k,
                use_hybrid=True,
                use_rerank=True,
                filter_dict=category_filter
            )
        else:
            # Fallback to basic semantic search with filter
            retrieved_docs = vector_store.search(user_input, k=k, filter_dict=category_filter)
        
        retrieval_time = time.time() - retrieval_start
        print(f"[TIMING] Retrieval: {retrieval_time:.2f}s ({len(retrieved_docs) if retrieved_docs else 0} docs)")
        
        if not retrieved_docs:
            return {
                "response": "I couldn't find relevant information in the legal documents for your query. Please try rephrasing your question or ask about a specific law, article, or legal topic.",
                "sources": [],
                "context_used": False
            }
        
        # ── Step 2: Context Building ──
        context_start = time.time()
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
        context_time = time.time() - context_start
        print(f"[TIMING] Context build: {context_time:.3f}s ({len(context)} chars)")
        
        # Create enhanced prompt with context
        enhanced_prompt = f"""Context from Pakistani legal documents:

{context}

---

User Question: {user_input}

Answer the question using the context above. Cite specific legal sections and articles by name (e.g., "Article 25", "Section 302 PPC"). Do NOT reference document numbers, file names, or page numbers in your answer."""
        
        # ── Step 3: LLM Generation ──
        # Build category-aware system prompt so the model knows its scope
        system_prompt = build_rag_system_prompt(category)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=enhanced_prompt)
        ]
        
        llm_start = time.time()
        try:
            chat_primary = _get_llm_primary()
            response = chat_primary.invoke(messages)
            llm_time = time.time() - llm_start
            total_time = time.time() - total_start
            print(f"[TIMING] LLM ({primary_model}): {llm_time:.2f}s")
            print(f"[TIMING] ── TOTAL: {total_time:.2f}s (retrieval={retrieval_time:.2f}s + context={context_time:.3f}s + llm={llm_time:.2f}s)")
            
            return {
                "response": response.content,
                "sources": sources,
                "context_used": True
            }
            
        except Exception as e1:
            print(f"Primary model failed ({time.time() - llm_start:.2f}s): {str(e1)}")
            try:
                llm_fallback_start = time.time()
                chat_fallback = _get_llm_fallback()
                response = chat_fallback.invoke(messages)
                llm_time = time.time() - llm_fallback_start
                total_time = time.time() - total_start
                print(f"[TIMING] LLM Fallback ({fallback_model}): {llm_time:.2f}s")
                print(f"[TIMING] ── TOTAL (fallback): {total_time:.2f}s")
                
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