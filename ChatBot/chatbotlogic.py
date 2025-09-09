import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

# Load environment variables from .env file
load_dotenv()

class SimpleChatbot:
    def __init__(self, model="llama-3.1-8b-instant", temperature=0.7):
        """
        Initialize the chatbot with Groq's open-source LLM
        
        Args:
            model (str): Model name (llama3-8b-8192, mixtral-8x7b-32768, etc.)
            temperature (float): Randomness in responses (0.0 to 1.0)
        """
        # Get API key from environment variables
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")
        
        # Initialize the Groq language model
        self.llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=1000  # Limit response length
        )
        
        # Store configuration for reference
        self.model_name = model
        self.temperature = temperature
        
        # System message to set chatbot behavior
        self.system_message = SystemMessage(
            content="""You are a helpful, friendly, and knowledgeable AI assistant. 
            You should:
            - Give clear, concise, and accurate answers
            - Be polite and professional
            - If you don't know something, admit it honestly
            - Provide helpful information and context when appropriate
            - Keep responses conversational but informative
            - Answer in a natural, human-like way"""
        )
    
    def get_response(self, user_input):
        """
        Get response from the chatbot for user input
        
        Args:
            user_input (str): User's question/message
            
        Returns:
            str: Chatbot's response
        """
        try:
            # Create messages list with system message and user input
            messages = [
                self.system_message,
                HumanMessage(content=user_input)
            ]
            
            # Get response from the model
            response = self.llm.invoke(messages)
            
            # Return the content of the response
            return response.content
            
        except Exception as e:
            # Handle errors gracefully
            return f"I'm sorry, I encountered an error: {str(e)}. Please try again."
    
    def get_streaming_response(self, user_input):
        """
        Get streaming response from the chatbot (for real-time typing effect)
        
        Args:
            user_input (str): User's question/message
            
        Yields:
            str: Chunks of the response
        """
        try:
            messages = [
                self.system_message,
                HumanMessage(content=user_input)
            ]
            
            # Stream the response
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            yield f"I'm sorry, I encountered an error: {str(e)}. Please try again."
    
    def update_system_message(self, new_system_message):
        """
        Update the system message to change chatbot behavior
        
        Args:
            new_system_message (str): New system message
        """
        self.system_message = SystemMessage(content=new_system_message)
    
    def get_model_info(self):
        """
        Get information about the current model configuration
        
        Returns:
            dict: Model configuration details
        """
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": 1000,
            "provider": "Groq"
        }

# Alternative class for different open-source models
class HuggingFaceChatbot:
    def __init__(self, model="microsoft/DialoGPT-medium", temperature=0.7):
        """
        Initialize chatbot with HuggingFace transformers (runs locally)
        Note: This requires more setup and computational resources
        """
        try:
            from langchain_huggingface import HuggingFacePipeline
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        except ImportError:
            raise ImportError("Please install transformers and torch: pip install transformers torch")
        
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model)
        model = AutoModelForCausalLM.from_pretrained(model)
        
        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=512,
            temperature=temperature
        )
        
        # Initialize LangChain wrapper
        self.llm = HuggingFacePipeline(pipeline=pipe)
        self.model_name = model
        self.temperature = temperature
    
    def get_response(self, user_input):
        """Get response using local HuggingFace model"""
        try:
            response = self.llm.invoke(user_input)
            return response
        except Exception as e:
            return f"I'm sorry, I encountered an error: {str(e)}. Please try again."

# Alternative class for Ollama (local models)
class OllamaChatbot:
    def __init__(self, model="llama2", temperature=0.7):
        """
        Initialize chatbot with Ollama (local open-source models)
        Requires Ollama to be installed and running locally
        """
        try:
            from langchain_community.llms import Ollama
        except ImportError:
            raise ImportError("Please install langchain-community: pip install langchain-community")
        
        self.llm = Ollama(
            model=model,
            temperature=temperature
        )
        
        self.model_name = model
        self.temperature = temperature
        
        self.system_message = "You are a helpful AI assistant. Give clear and concise answers."
    
    def get_response(self, user_input):
        """Get response using Ollama local model"""
        try:
            # Combine system message with user input
            full_prompt = f"{self.system_message}\n\nUser: {user_input}\nAssistant:"
            response = self.llm.invoke(full_prompt)
            return response
        except Exception as e:
            return f"I'm sorry, I encountered an error: {str(e)}. Please try again."