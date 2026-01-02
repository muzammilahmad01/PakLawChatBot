"""
Test script to verify API keys and packages
"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("API Key Validation Test")
print("=" * 60)

# Load environment variables
load_dotenv()

# Check GROQ API Key
groq_key = os.getenv("GROQ_API_KEY")
print(f"\n1. GROQ_API_KEY:")
if groq_key:
    print(f"   [OK] Found (length: {len(groq_key)})")
    print(f"   Preview: {groq_key[:10]}...{groq_key[-10:]}")
else:
    print("   [ERROR] NOT FOUND")

# Check GEMINI API Key
gemini_key = os.getenv("GEMINI_API_KEY")
print(f"\n2. GEMINI_API_KEY:")
if gemini_key:
    print(f"   [OK] Found (length: {len(gemini_key)})")
    print(f"   Preview: {gemini_key[:10]}...{gemini_key[-10:]}")
else:
    print("   [ERROR] NOT FOUND")

# Check model settings
primary = os.getenv("MODEL_PRIMARY")
fallback = os.getenv("MODEL_FALLBACK")
print(f"\n3. Model Settings:")
print(f"   PRIMARY: {primary}")
print(f"   FALLBACK: {fallback}")

# Test Groq import
print(f"\n4. Testing Groq package:")
try:
    from langchain_groq import ChatGroq
    print("   [OK] langchain-groq installed")
    
    # Try to initialize (won't call API, just check initialization)
    if groq_key:
        try:
            chat = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=groq_key,
                temperature=0.7
            )
            print("   [OK] ChatGroq initialized successfully")
        except Exception as e:
            print(f"   [ERROR] ChatGroq initialization failed: {str(e)}")
except ImportError as e:
    print(f"   [ERROR] langchain-groq NOT installed: {str(e)}")

# Test Google Embeddings import
print(f"\n5. Testing Google Embeddings package:")
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    print("   [OK] langchain-google-genai installed")
    
    # Try to initialize
    if gemini_key:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=gemini_key
            )
            print("   [OK] GoogleGenerativeAIEmbeddings initialized successfully")
        except Exception as e:
            print(f"   [ERROR] Embeddings initialization failed: {str(e)}")
except ImportError as e:
    print(f"   [ERROR] langchain-google-genai NOT installed: {str(e)}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
