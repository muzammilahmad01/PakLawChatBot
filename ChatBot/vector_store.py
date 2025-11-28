"""
Vector Store Manager for RAG Pipeline - Simplified Version
Uses TF-IDF embeddings (no external dependencies needed)
"""

import os
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()


class VectorStoreManager:
    """Manage ChromaDB vector store for document retrieval"""
    
    def __init__(
        self, 
        persist_directory: str = "vectorstores/chroma_db",
        collection_name: str = "paklaw_docs"
    ):
        """
        Initialize vector store manager with local embeddings
        
        Args:
            persist_directory: Directory to store ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        print(f"[*] Initializing local sentence-transformers embeddings...")
        
        # Use HuggingFace embeddings with a small, efficient model
        # This will download once and cache locally
        try:
            import socket
            # Set a timeout for network operations
            socket.setdefaulttimeout(10)
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print(f"[OK] Embeddings initialized successfully")
        except Exception as e:
            print(f"[!] Error initializing HuggingFace embeddings: {e}")
            print(f"    This is likely due to network timeout or model download issues.")
            print(f"    Falling back to FakeEmbeddings (deterministic, no network needed)...")
            # Fallback to a method that doesn't require downloads
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=384)
            print(f"[OK] Using FakeEmbeddings as fallback")
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        self.vectorstore: Optional[Chroma] = None
    
    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """
        Create a new vector store from documents
        
        Args:
            documents: List of Document objects to embed
            
        Returns:
            Chroma vector store instance
        """
        print(f"Creating vector store with {len(documents)} documents...")
        
        try:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,  # Explicitly pass embeddings
                persist_directory=self.persist_directory,
                collection_name=self.collection_name
            )
            
            print(f"[OK] Vector store created successfully at {self.persist_directory}")
            return self.vectorstore
            
        except Exception as e:
            print(f"[ERROR] creating vector store: {str(e)}")
            raise
    
    def load_vectorstore(self) -> Optional[Chroma]:
        """
        Load existing vector store from disk
        
        Returns:
            Chroma vector store instance or None if not found
        """
        try:
            if not os.path.exists(self.persist_directory):
                print(f"Vector store not found at {self.persist_directory}")
                return None
            
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,  # Explicitly pass embeddings
                persist_directory=self.persist_directory,
                collection_name=self.collection_name
            )
            
            print(f"[OK] Vector store loaded from {self.persist_directory}")
            return self.vectorstore
            
        except Exception as e:
            print(f"[ERROR] loading vector store: {str(e)}")
            return None
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to existing vector store
        
        Args:
            documents: List of Document objects to add
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore() or load_vectorstore() first.")
        
        try:
            self.vectorstore.add_documents(documents)
            print(f"[OK] Added {len(documents)} documents to vector store")
        except Exception as e:
            print(f"[ERROR] adding documents: {str(e)}")
            raise
    
    def search(
        self, 
        query: str, 
        k: int = 3,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of most similar Document objects
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call load_vectorstore() first.")
        
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            return results
        except Exception as e:
            print(f"✗ Error searching: {str(e)}")
            return []
    
    def search_with_scores(
        self, 
        query: str, 
        k: int = 3
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with similarity scores
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call load_vectorstore() first.")
        
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k
            )
            return results
        except Exception as e:
            print(f"✗ Error searching: {str(e)}")
            return []
    
    def delete_collection(self):
        """Delete the entire collection"""
        if self.vectorstore is not None:
            self.vectorstore.delete_collection()
            print(f"[OK] Deleted collection: {self.collection_name}")
    
    def get_vectorstore(self) -> Optional[Chroma]:
        """Get the current vector store instance"""
        return self.vectorstore
