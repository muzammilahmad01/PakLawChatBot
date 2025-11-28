"""
Document Ingestion Script for RAG Pipeline
Processes PDFs and creates/updates vector store
"""

import os
import sys
from document_processor import DocumentProcessor
from vector_store import VectorStoreManager


def ingest_test_pdf():
    """Ingest the test PDF (Pakistan's Constitution)"""
    
    print("=" * 60)
    print("RAG Pipeline - Document Ingestion (Test Mode)")
    print("=" * 60)
    
    # Path to test PDF (relative to ChatBot directory)
    test_pdf = "../data/test_data/Pakistan's Constituion.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"\n[ERROR] Test PDF not found at {test_pdf}")
        return False
    
    print(f"\n[*] Processing: {os.path.basename(test_pdf)}")
    print(f"    Size: {os.path.getsize(test_pdf) / 1024 / 1024:.2f} MB\n")
    
    try:
        # Step 1: Process PDF
        print("Step 1: Loading and chunking PDF...")
        print("-" * 60)
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        chunks = processor.process_pdf(test_pdf)
        
        if not chunks:
            print("\n✗ No chunks created. Aborting.")
            return False
        
        print(f"\n✓ Created {len(chunks)} chunks")
        
        # Show sample chunk
        print("\n[Sample chunk]:")
        print(f"   Content preview: {chunks[0].page_content[:150]}...")
        print(f"   Metadata: {chunks[0].metadata}")
        
        # Step 2: Create vector store
        print("\n\nStep 2: Creating vector store with embeddings...")
        print("-" * 60)
        print("[!] Initializing embeddings (may take a moment on first run)...\n")
        
        manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_test",
            collection_name="pakistan_constitution"
        )
        
        manager.create_vectorstore(chunks)
        
        # Step 3: Test retrieval
        print("\n\nStep 3: Testing retrieval...")
        print("-" * 60)
        
        test_queries = [
            "What are fundamental rights in Pakistan?",
            "What is the role of the President?",
            "How is the judiciary structured?"
        ]
        
        for query in test_queries:
            print(f"\n[?] Query: \"{query}\"")
            results = manager.search(query, k=2)
            
            if results:
                print(f"   ✓ Found {len(results)} relevant chunks")
                print(f"   Top result preview: {results[0].page_content[:100]}...")
                print(f"   Source: {results[0].metadata.get('source', 'Unknown')}, Page: {results[0].metadata.get('page', 'N/A')}")
            else:
                print("   ✗ No results found")
        
        # Success summary
        print("\n\n" + "=" * 60)
        print("[SUCCESS] INGESTION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"[Summary]:")
        print(f"   - PDF processed: {os.path.basename(test_pdf)}")
        print(f"   - Total chunks: {len(chunks)}")
        print(f"   - Vector store: vectorstores/chroma_db_test")
        print(f"   - Collection: pakistan_constitution")
        print("\n[OK] Ready to integrate with chatbot!")
        
        return True
        
    except Exception as e:
        print(f"\n\n[ERROR] during ingestion:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def ingest_full_dataset():
    """Ingest all 320 PDFs from FYP_DATA (for later use)"""
    
    print("=" * 60)
    print("RAG Pipeline - Full Dataset Ingestion")
    print("=" * 60)
    
    data_dir = "../FYP_DATA/kpk_laws"
    
    if not os.path.exists(data_dir):
        print(f"\n[ERROR] Data directory not found at {data_dir}")
        return False
    
    print(f"\n[*] Processing all PDFs from: {data_dir}")
    print("[!] This will take several minutes...\n")
    
    try:
        # Step 1: Process all PDFs
        print("Step 1: Loading and chunking all PDFs...")
        print("-" * 60)
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        chunks = processor.process_directory(data_dir, recursive=True)
        
        if not chunks:
            print("\n[ERROR] No chunks created. Aborting.")
            return False
        
        # Step 2: Create vector store
        print("\n\nStep 2: Creating vector store...")
        print("-" * 60)
        print("[!] Initializing embeddings (may take a moment on first run)...\n")
        
        manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_full",
            collection_name="kpk_laws_full"
        )
        
        manager.create_vectorstore(chunks)
        
        # Success summary
        print("\n\n" + "=" * 60)
        print("[SUCCESS] FULL DATASET INGESTION COMPLETED")
        print("=" * 60)
        print(f"[Summary]:")
        print(f"   - Total chunks: {len(chunks)}")
        print(f"   - Vector store: vectorstores/chroma_db_full")
        print(f"   - Collection: kpk_laws_full")
        
        return True
        
    except Exception as e:
        print(f"\n\n[ERROR] during ingestion:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Default: Run test ingestion
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    if mode == "test":
        success = ingest_test_pdf()
    elif mode == "full":
        success = ingest_full_dataset()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python ingest_documents.py [test|full]")
        success = False
    
    sys.exit(0 if success else 1)
