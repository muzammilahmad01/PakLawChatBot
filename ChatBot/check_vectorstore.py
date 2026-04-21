"""
Quick tool to check if all embeddings are stored in the vector store.
Compares source PDFs vs embedded chunks per category.

Usage: python check_vectorstore.py
"""

import os
from vector_store import VectorStoreManager


def check():
    print("=" * 65)
    print("  VECTOR STORE HEALTH CHECK")
    print("=" * 65)
    
    # 1. Load vector store
    print("\n[*] Loading vector store...")
    vs = VectorStoreManager(
        persist_directory="vectorstores/chroma_db_full",
        collection_name="paklaw_docs"
    )
    
    if vs.load_vectorstore() is None:
        print("[ERROR] Vector store not found! Run ingestion first.")
        return
    
    collection = vs.vectorstore._collection
    total_chunks = collection.count()
    print(f"[OK] Total chunks in store: {total_chunks}")
    
    # 2. Get chunks per category from vector store
    print("\n[*] Reading metadata from vector store...")
    results = collection.get(include=["metadatas"])
    
    store_counts = {}
    for meta in results["metadatas"]:
        dept = meta.get("department", "unknown")
        store_counts[dept] = store_counts.get(dept, 0) + 1
    
    # 3. Count PDFs per category from source data
    data_dir = "../data/pakistan_code"
    source_counts = {}
    
    if os.path.exists(data_dir):
        for category in sorted(os.listdir(data_dir)):
            cat_path = os.path.join(data_dir, category)
            if os.path.isdir(cat_path):
                pdf_count = len([f for f in os.listdir(cat_path) if f.lower().endswith('.pdf')])
                source_counts[category] = pdf_count
    
    # 4. Show comparison
    all_categories = sorted(set(list(source_counts.keys()) + list(store_counts.keys())))
    
    print(f"\n{'Category':<30} {'PDFs':>6} {'Chunks':>8} {'Status':>10}")
    print("-" * 65)
    
    embedded_count = 0
    not_embedded_count = 0
    
    for cat in all_categories:
        pdfs = source_counts.get(cat, 0)
        chunks = store_counts.get(cat, 0)
        
        if chunks > 0:
            status = "✅ DONE"
            embedded_count += 1
        else:
            status = "❌ PENDING"
            not_embedded_count += 1
        
        print(f"  {cat:<28} {pdfs:>6} {chunks:>8} {status:>10}")
    
    # 5. Summary
    print("-" * 65)
    print(f"\n  Total categories:  {len(all_categories)}")
    print(f"  Embedded:          {embedded_count} ✅")
    print(f"  Pending:           {not_embedded_count} ❌")
    print(f"  Total chunks:      {total_chunks}")
    
    if not_embedded_count == 0:
        print(f"\n  🎉 ALL CATEGORIES ARE FULLY EMBEDDED!")
    else:
        print(f"\n  ⚠️  {not_embedded_count} categories still need embedding.")
        print(f"  Run: python ingest_documents.py fresh")


if __name__ == "__main__":
    check()
