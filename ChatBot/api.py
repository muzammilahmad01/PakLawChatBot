from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from chatbotlogic import get_rag_response, get_basic_response, load_vector_store, get_hybrid_retriever

# Create FastAPI app
app = FastAPI(title="PakLaw ChatBot API")

# ─── PRELOAD AT STARTUP ───
# Load embeddings + vector store + hybrid retriever ONCE when server starts.
# This avoids the 30-45s delay on the first user request.
@app.on_event("startup")
async def startup_preload():
    print("[*] Preloading vector store and embeddings at startup...")
    vs = load_vector_store()
    if vs:
        print("[OK] Vector store loaded at startup")
        retriever = get_hybrid_retriever()
        if retriever:
            print("[OK] Hybrid retriever ready at startup")
    else:
        print("[WARN] Vector store not available — will use basic mode")

# Allow React frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Category to law_type mapping
# Values MUST match the 'department' metadata in the vector store (case-sensitive!)
CATEGORY_FILTER_MAP = {
    "cyber": "Pta_Laws",                # PTA/Cyber laws (1984 chunks)
    "criminal": "Criminal_Laws",        # Criminal Laws (1109 chunks)
    "Family": "Family_Laws",            # Family Laws (455 chunks)
    "labour": "Labour_Laws",            # Labour Laws (1584 chunks)
    "Property": "Land_Property_Laws",   # Property Laws (416 chunks)
    "constitutional": None,             # Constitution (no filter, search all)
    "general": None,                    # General query (no filter, search all)
}

# Request model
class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    category: Optional[str] = None  # Category for filtering

# Response model
class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    context_used: bool = False

@app.get("/")
async def root():
    return {"message": "PakLaw ChatBot API is running!"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages and return responses from RAG pipeline"""
    try:
        if request.use_rag:
            # Get filter based on category
            category_filter = None
            if request.category and request.category in CATEGORY_FILTER_MAP:
                filter_value = CATEGORY_FILTER_MAP[request.category]
                if filter_value:
                    category_filter = {"department": filter_value}
            
            result = get_rag_response(
                request.message,
                category_filter=category_filter,
                category=request.category  # pass category name for prompt awareness
            )
            return ChatResponse(
                response=result["response"],
                sources=result.get("sources", []),
                context_used=result.get("context_used", False)
            )
        else:
            response = get_basic_response(request.message)
            return ChatResponse(response=response)
    except Exception as e:
        return ChatResponse(
            response=f"Sorry, an error occurred: {str(e)}",
            sources=[],
            context_used=False
        )