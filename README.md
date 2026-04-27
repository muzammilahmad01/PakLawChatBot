## 🆕 RAG (Retrieval Augmented Generation)

The chatbot now uses RAG to answer questions based on actual Pakistani law documents!

### Features:
- 📚 Document-based answers with source citations
- 🔍 Semantic search using HuggingFace embeddings
- 📄 Supports PDF ingestion and chunking
- 💾 ChromaDB vector store for efficient retrieval
- 🎚️ Toggle RAG on/off in the UI

### Setup:
1. Install dependencies: `pip install -r requirements.txt`
2. Add your GROQ_API_KEY to `.env`
3. Ingest documents: `python ChatBot/ingest_documents.py test`
4. Run the app: `streamlit run ChatBot/app.py`



doing changes in readme to tets CI/CD Pipeline
