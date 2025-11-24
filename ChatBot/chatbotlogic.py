from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

# Load API key and models from .env
# Note: The key is loaded automatically by ChatGoogleGenerativeAI if set as GEMINI_API_KEY
gemini_api_key = os.getenv("GEMINI_API_KEY") 
primary_model = os.getenv("MODEL_PRIMARY", "gemini-2.5-pro")
fallback_model = os.getenv("MODEL_FALLBACK", "gemini-2.5-flash")

# System prompt for the legal assistant persona
SYSTEM_PROMPT = (
    "You are a helpful legal assistant chatbot specializing in Pakistani law. "
    "Provide clear, concise, and accurate information about Pakistani legal matters, "
    "procedures, and general legal concepts. Always include relevant sources and "
    "remind users to consult with qualified lawyers for specific legal advice."
)


def get_chatbot_response(user_input: str) -> str:
    """
    Generate a response using Gemini API with fallback model support.
    """
    if not gemini_api_key:
        return "⚠️ GEMINI_API_KEY is missing. Please set it in your .env file."
    
    # Define the conversation history with the system prompt
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    try:
        # Try with primary model (e.g., gemini-2.5-pro for better reasoning)
        chat_primary = ChatGoogleGenerativeAI(
            model=primary_model, 
            google_api_key=gemini_api_key, 
            temperature=0.7
        )
        response = chat_primary.invoke(messages)
        
        return response.content
        
    except Exception as e1:
        print(f"Primary model ({primary_model}) failed: {str(e1)}")
        try:
            # If primary fails, switch to fallback (e.g., gemini-2.5-flash for speed/cost)
            chat_fallback = ChatGoogleGenerativeAI(
                model=fallback_model, 
                google_api_key=gemini_api_key,
                temperature=0.7
            )
            response = chat_fallback.invoke(messages)
            
            # Indicate that the fallback model was used (optional, for debugging)
            return f" (via Fallback) {response.content}"
            
        except Exception as e2:
            return f"⚠️ Both models failed.\nPrimary error: {str(e1)}\nFallback error: {str(e2)}"

# Keep this for compatibility
def get_response(user_input: str) -> str:
    return get_chatbot_response(user_input)