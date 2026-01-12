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
    test_pdf = "../data/Pakistan's Constituion.pdf"
    
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
    """Ingest all PDFs from data/kpk_laws (45 departments)"""
    
    print("=" * 60)
    print("RAG Pipeline - Full Dataset Ingestion")
    print("=" * 60)
    
    data_dir = "../data/kpk_laws"
    
    if not os.path.exists(data_dir):
        print(f"\n[ERROR] Data directory not found at {data_dir}")
        return False
    
    print(f"\n[*] Scanning for PDFs in: {data_dir}")
    
    # First, collect all PDF paths
    pdf_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    total_pdfs = len(pdf_files)
    print(f"[*] Found {total_pdfs} PDF files to process")
    print("[!] This will take several minutes...\n")
    
    if total_pdfs == 0:
        print("[ERROR] No PDF files found!")
        return False
    
    try:
        # Step 1: Process PDFs with progress tracking
        print("Step 1: Loading and chunking all PDFs...")
        print("-" * 60)
        
        from document_processor import DocumentProcessor
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        
        all_chunks = []
        successful = 0
        failed = 0
        failed_files = []
        
        for i, pdf_path in enumerate(pdf_files, 1):
            pdf_name = os.path.basename(pdf_path)
            dept_name = os.path.basename(os.path.dirname(pdf_path))
            
            try:
                # Show progress
                print(f"\n[{i}/{total_pdfs}] Processing: {pdf_name[:50]}...")
                print(f"    Department: {dept_name}")
                
                chunks = processor.process_pdf(pdf_path)
                
                if chunks:
                    # Add department metadata
                    for chunk in chunks:
                        chunk.metadata['department'] = dept_name
                    
                    all_chunks.extend(chunks)
                    successful += 1
                    print(f"    [OK] Created {len(chunks)} chunks")
                else:
                    failed += 1
                    failed_files.append(pdf_name)
                    print(f"    [WARN] No chunks created")
                    
            except Exception as e:
                failed += 1
                failed_files.append(pdf_name)
                print(f"    [ERROR] Failed: {str(e)[:50]}")
                continue  # Skip to next PDF
        
        print("\n" + "-" * 60)
        print(f"[Summary] Processed: {successful}/{total_pdfs} PDFs successfully")
        print(f"          Total chunks: {len(all_chunks)}")
        if failed > 0:
            print(f"          Failed: {failed} PDFs")
        
        if not all_chunks:
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
        
        # Process in batches to avoid memory issues
        batch_size = 500
        total_batches = (len(all_chunks) + batch_size - 1) // batch_size
        
        print(f"[*] Creating vector store with {len(all_chunks)} chunks in {total_batches} batches...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(all_chunks))
            batch = all_chunks[start_idx:end_idx]
            
            print(f"\n[Batch {batch_num + 1}/{total_batches}] Processing chunks {start_idx + 1} to {end_idx}...")
            
            if batch_num == 0:
                # Create new vector store with first batch
                manager.create_vectorstore(batch)
            else:
                # Add subsequent batches
                manager.add_documents(batch)
        
        # Success summary
        print("\n\n" + "=" * 60)
        print("[SUCCESS] FULL DATASET INGESTION COMPLETED")
        print("=" * 60)
        print(f"[Summary]:")
        print(f"   - PDFs processed: {successful}/{total_pdfs}")
        print(f"   - Total chunks: {len(all_chunks)}")
        print(f"   - Vector store: vectorstores/chroma_db_full")
        print(f"   - Collection: kpk_laws_full")
        
        if failed_files:
            print(f"\n[WARN] Failed files ({len(failed_files)}):")
            for f in failed_files[:5]:  # Show first 5
                print(f"   - {f}")
            if len(failed_files) > 5:
                print(f"   ... and {len(failed_files) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"\n\n[ERROR] during ingestion:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def ingest_additional_laws(folders=None):
    """
    Append additional law folders (PTA, NADRA) to existing vector store.
    This does NOT re-process existing data - only adds new documents.
    """
    
    print("=" * 60)
    print("RAG Pipeline - Append Additional Laws")
    print("=" * 60)
    
    # Default folders to ingest
    if folders is None:
        folders = ["pta_laws", "nadra_laws"]
    
    base_data_dir = "../data"
    
    try:
        # Step 1: Load existing vector store
        print("\n[*] Loading existing vector store...")
        from vector_store import VectorStoreManager
        from document_processor import DocumentProcessor
        
        vs_manager = VectorStoreManager(
            persist_directory="vectorstores/chroma_db_full",
            collection_name="paklaw_docs"
        )
        
        if not vs_manager.load_vectorstore():
            print("[ERROR] Could not load existing vector store!")
            print("        Please run 'python ingest_documents.py full' first.")
            return False
        
        # Get current count
        initial_count = vs_manager.vectorstore._collection.count()
        print(f"[*] Current chunks in store: {initial_count}")
        
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        
        total_new_chunks = 0
        
        # Step 2: Process each folder
        for folder_name in folders:
            folder_path = os.path.join(base_data_dir, folder_name)
            
            if not os.path.exists(folder_path):
                print(f"\n[SKIP] Folder not found: {folder_path}")
                continue
            
            print(f"\n{'='*60}")
            print(f"Processing: {folder_name.upper()}")
            print(f"Path: {folder_path}")
            print("=" * 60)
            
            # Collect PDFs recursively
            pdf_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            print(f"[*] Found {len(pdf_files)} PDF files")
            
            if len(pdf_files) == 0:
                print(f"[WARN] No PDFs in {folder_name}")
                continue
            
            # Process each PDF
            folder_chunks = []
            successful = 0
            failed = 0
            
            for i, pdf_path in enumerate(pdf_files, 1):
                pdf_name = os.path.basename(pdf_path)
                # Get category from subfolder
                rel_path = os.path.relpath(pdf_path, folder_path)
                category = os.path.dirname(rel_path) if os.path.dirname(rel_path) else folder_name
                
                try:
                    print(f"  [{i}/{len(pdf_files)}] {pdf_name[:45]}...", end=" ")
                    
                    chunks = processor.process_pdf(pdf_path)
                    
                    if chunks:
                        # Add metadata
                        for chunk in chunks:
                            chunk.metadata['department'] = folder_name
                            chunk.metadata['category'] = category
                            chunk.metadata['law_type'] = folder_name.replace('_laws', '').upper()
                        
                        folder_chunks.extend(chunks)
                        successful += 1
                        print(f"[OK] {len(chunks)} chunks")
                    else:
                        failed += 1
                        print("[WARN] No chunks")
                        
                except Exception as e:
                    failed += 1
                    print(f"[ERROR] {str(e)[:30]}")
                    continue
            
            # Add to vector store in batches
            if folder_chunks:
                print(f"\n[*] Adding {len(folder_chunks)} chunks to vector store...")
                
                batch_size = 500
                for i in range(0, len(folder_chunks), batch_size):
                    batch = folder_chunks[i:i + batch_size]
                    vs_manager.add_documents(batch)
                    print(f"    Added batch {i//batch_size + 1}/{(len(folder_chunks)-1)//batch_size + 1}")
                
                total_new_chunks += len(folder_chunks)
            
            print(f"\n[DONE] {folder_name}: {successful} PDFs, {len(folder_chunks)} chunks")
        
        # Final summary
        final_count = vs_manager.vectorstore._collection.count()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] INGESTION COMPLETE")
        print("=" * 60)
        print(f"  Previous chunks: {initial_count}")
        print(f"  New chunks added: {total_new_chunks}")
        print(f"  Total chunks now: {final_count}")
        
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
    elif mode == "append":
        # Append PTA and NADRA laws to existing store
        success = ingest_additional_laws()
    elif mode == "pta":
        # Only append PTA laws
        success = ingest_additional_laws(["pta_laws"])
    elif mode == "nadra":
        # Only append NADRA laws
        success = ingest_additional_laws(["nadra_laws"])
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python ingest_documents.py [test|full|append|pta|nadra]")
        print("  test   - Ingest single test PDF")
        print("  full   - Ingest all KPK laws (creates new store)")
        print("  append - Append PTA + NADRA laws to existing store")
        print("  pta    - Append only PTA laws")
        print("  nadra  - Append only NADRA laws")
        success = False
    
    sys.exit(0 if success else 1)

