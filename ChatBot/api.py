from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from chatbotlogic import get_rag_response, get_basic_response

# Create FastAPI app
app = FastAPI(title="PakLaw ChatBot API")

# Allow React frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True

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
            result = get_rag_response(request.message)
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