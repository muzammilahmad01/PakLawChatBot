"""Quick diagnostic - check vector store departments and search"""
from vector_store import VectorStoreManager

print("Loading vector store...")
vs = VectorStoreManager(
    persist_directory="vectorstores/chroma_db_full",
    collection_name="paklaw_docs"
)
store = vs.load_vectorstore()

if not store:
    print("FAILED to load vector store!")
    exit(1)

col = vs.vectorstore._collection
print(f"Total chunks: {col.count()}")

# Get all unique departments
print("\nFetching all metadata...")
all_meta = col.get(include=["metadatas"])
depts = {}
for m in all_meta.get("metadatas", []):
    d = m.get("department", "NO_DEPT")
    depts[d] = depts.get(d, 0) + 1

print(f"\nUnique department values ({len(depts)}):")
for d in sorted(depts.keys()):
    print(f"  '{d}' -> {depts[d]} chunks")

# Test search WITHOUT filter
print("\n" + "="*50)
print("TEST 1: Search WITHOUT filter")
results = vs.search("What are fundamental rights in Pakistan?", k=3)
print(f"Results: {len(results)}")
for i, r in enumerate(results):
    print(f"  [{i+1}] dept='{r.metadata.get('department', '?')}' | {r.page_content[:100]}")

# Test search WITH criminal_laws filter
print("\n" + "="*50)
print("TEST 2: Search WITH filter department=criminal_laws")
results2 = vs.search("bail procedures", k=3, filter_dict={"department": "criminal_laws"})
print(f"Results: {len(results2)}")
for i, r in enumerate(results2):
    print(f"  [{i+1}] dept='{r.metadata.get('department', '?')}' | {r.page_content[:100]}")

# Test search WITH no filter for bail
print("\n" + "="*50)
print("TEST 3: Search 'bail procedures' WITHOUT filter")
results3 = vs.search("bail procedures in Pakistan", k=3)
print(f"Results: {len(results3)}")
for i, r in enumerate(results3):
    print(f"  [{i+1}] dept='{r.metadata.get('department', '?')}' | {r.page_content[:100]}")
