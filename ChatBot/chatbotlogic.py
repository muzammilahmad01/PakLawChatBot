import os
import requests
import json
from dotenv import load_dotenv

# ✅ Load environment variables at the start
load_dotenv()

# Get Perplexity API key (change this line)
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

if not perplexity_api_key:
    raise ValueError("⚠️ PERPLEXITY_API_KEY is missing. Please set it in your .env file.")

# Remove the old LangChain and Groq imports/setup
# Replace with Perplexity API endpoint
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
SELECTED_MODEL = "sonar-pro"

# Replace your old get_chatbot_response function with this:
def get_chatbot_response(user_input: str) -> str:
    """
    Takes user input and returns chatbot response using Perplexity API.
    """
    try:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {perplexity_api_key}"
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
            PERPLEXITY_API_URL,
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

# Keep this for backward compatibility
def get_response(user_input: str) -> str:
    return get_chatbot_response(user_input)

# Testing section (optional)
if __name__ == "__main__":
    print("🤖 PakLaw ChatBot - Testing Mode (Perplexity API)")
    while True:
        user_inp = input("You: ")
        if user_inp.lower() in ["quit", "exit", "bye"]:
            print("Chatbot: Goodbye 👋")
            break
        bot_resp = get_chatbot_response(user_inp)
        print(f"Chatbot: {bot_resp}")
        print("-" * 40)