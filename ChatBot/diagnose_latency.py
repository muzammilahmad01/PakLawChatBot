import time
import os
import sys

print("[*] Starting latency diagnosis...")

start_total = time.time()

t0 = time.time()
try:
    from chatbotlogic import load_vector_store, get_hybrid_retriever, get_rag_response
except ImportError as e:
    print(f"[!] Import error: {e}")
    sys.exit(1)
print(f"[+] Imports took: {time.time() - t0:.2f}s")

t0 = time.time()
print("[*] Loading vector store...")
vs = load_vector_store()
print(f"[+] load_vector_store took: {time.time() - t0:.2f}s")

t0 = time.time()
print("[*] Initializing hybrid retriever...")
hr = get_hybrid_retriever()
print(f"[+] get_hybrid_retriever took: {time.time() - t0:.2f}s")

t0 = time.time()
print("[*] Running first query: 'What is a cyber crime?'")
res1 = get_rag_response("What is a cyber crime?", k=3)
print(f"[+] First query took: {time.time() - t0:.2f}s")
print(f"    Response preview: {res1.get('response', 'ERROR')[:100]}")

t0 = time.time()
print("[*] Running second query: 'Tell me about bail in criminal court'")
res2 = get_rag_response("Tell me about bail in criminal court", k=3)
print(f"[+] Second query took: {time.time() - t0:.2f}s")
print(f"    Response preview: {res2.get('response', 'ERROR')[:100]}")

print(f"\n[=] Total diagnosis time: {time.time() - start_total:.2f}s")
