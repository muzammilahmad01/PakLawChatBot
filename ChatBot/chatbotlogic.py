import os
import requests
import json
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# Get Groq API key
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("⚠️ GROQ_API_KEY is missing. Please set it in your .env file.")

# Groq API endpoint & model
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
SELECTED_MODEL = "openai/gpt-oss-20b"

def get_chatbot_response(user_input: str) -> str:
    """
    Takes user input and returns chatbot response using Groq API.
    """
    try:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {groq_api_key}"
        }
        
        payload = {
            "model": SELECTED_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful legal assistant chatbot specializing in Pakistani law. "
                        "Provide clear, concise, and accurate information about Pakistani legal matters, "
                        "procedures, and general legal concepts. Always include relevant sources and "
                        "remind users to consult with qualified lawyers for specific legal advice."
                    )
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content.strip()
            else:
                return "⚠️ Sorry, I couldn't generate a proper response. Please try again."
        else:
            return f"⚠️ API request failed: {response.status_code}. Please check your API key."
            
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Keep this for compatibility
def get_response(user_input: str) -> str:
    return get_chatbot_response(user_input)

if __name__ == "__main__":
    print("🤖 PakLaw ChatBot - Testing Mode (Groq API)")
    while True:
        user_inp = input("You: ")
        if user_inp.lower() in ["quit", "exit", "bye"]:
            print("Chatbot: Goodbye 👋")
            break
        bot_resp = get_chatbot_response(user_inp)
        print(f"Chatbot: {bot_resp}")
        print("-" * 40)
