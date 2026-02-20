"""
Advanced Retriever for RAG Pipeline
Implements Hybrid Search (Semantic + BM25), Reranking, and Query Expansion
"""

import re
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document


# Pakistani Legal Synonym Map for Query Expansion
# Maps common terms to their legal equivalents and related terms
LEGAL_SYNONYMS = {
    # Criminal Law
    "theft": ["stealing", "robbery", "larceny", "PPC Section 379", "dishonest misappropriation"],
    "murder": ["homicide", "killing", "qatl", "PPC Section 302", "culpable homicide"],
    "robbery": ["theft", "dacoity", "extortion", "PPC Section 392"],
    "kidnapping": ["abduction", "PPC Section 359", "wrongful confinement"],
    "fraud": ["cheating", "forgery", "dishonesty", "PPC Section 420", "misrepresentation"],
    "bribery": ["corruption", "gratification", "NAB", "anti corruption"],
    "assault": ["hurt", "grievous hurt", "battery", "PPC Section 332"],
    "bail": ["surety", "bond", "CrPC Section 497", "pre-arrest bail", "post-arrest bail"],
    
    # Family Law
    "divorce": ["talaq", "khula", "dissolution of marriage", "family courts act"],
    "marriage": ["nikah", "Muslim Family Laws Ordinance", "marriage registration"],
    "custody": ["guardianship", "hizanat", "minor", "guardian and wards act"],
    "maintenance": ["nafaqa", "alimony", "financial support", "wife maintenance"],
    "inheritance": ["succession", "wirasat", "Islamic inheritance", "succession act"],
    "dower": ["haq mehr", "mahr", "mehr", "dowry"],
    
    # Property Law
    "property": ["land", "real estate", "immovable property", "transfer of property act"],
    "rent": ["tenancy", "lease", "landlord tenant", "rent restriction"],
    "land": ["property", "agricultural land", "revenue", "land revenue act"],
    "eviction": ["ejectment", "removal", "tenant eviction"],
    
    # Labour Law
    "wages": ["salary", "payment of wages act", "minimum wages", "remuneration"],
    "termination": ["dismissal", "removal from service", "wrongful termination"],
    "pension": ["retirement benefits", "gratuity", "provident fund"],
    "worker": ["employee", "labourer", "workman", "industrial worker"],
    
    # Constitutional
    "fundamental rights": ["basic rights", "constitutional rights", "Part II", "Article 8 to 28"],
    "freedom of speech": ["Article 19", "expression", "free speech", "press freedom"],
    "right to education": ["Article 25A", "free education", "compulsory education"],
    "equality": ["Article 25", "equal protection", "non-discrimination"],
    
    # Cyber/PTA
    "cybercrime": ["electronic crime", "PECA", "online crime", "cyber offence"],
    "data protection": ["privacy", "personal data", "information security"],
    "defamation": ["libel", "slander", "online defamation", "PPC Section 499"],
    
    # General Legal Terms
    "FIR": ["first information report", "police report", "complaint", "CrPC Section 154"],
    "appeal": ["revision", "review", "appellate", "high court appeal"],
    "writ": ["Article 199", "constitutional petition", "mandamus", "habeas corpus"],
    "injunction": ["stay order", "restraining order", "temporary injunction"],
    "evidence": ["proof", "witness", "Qanun-e-Shahadat", "testimony"],
    "contract": ["agreement", "contract act 1872", "breach of contract"],
    "tax": ["taxation", "income tax", "sales tax", "FBR", "revenue"],
    "company": ["corporation", "companies act", "SECP", "corporate"],
}


def expand_query(query: str) -> str:
    """
    Expand query with legal synonyms to improve retrieval.
    Returns the original query + relevant synonym terms appended.
    """
    query_lower = query.lower()
    expansions = []
    
    for term, synonyms in LEGAL_SYNONYMS.items():
        # Check if the term appears in the query
        if term in query_lower:
            # Add synonyms that aren't already in the query
            for synonym in synonyms:
                if synonym.lower() not in query_lower:
                    expansions.append(synonym)
    
    if expansions:
        # Limit to top 5 most relevant expansions to avoid noise
        expanded = query + " " + " ".join(expansions[:5])
        return expanded
    
    return query


class HybridRetriever:
    """
    Advanced retriever combining:
    1. Semantic Search (embeddings-based)
    2. BM25 Keyword Search (term-based)
    3. Reciprocal Rank Fusion (combining results)
    4. Optional reranking based on relevance scores
    """
    
    def __init__(self, vectorstore, documents: List[Document] = None):
        """
        Initialize hybrid retriever
        
        Args:
            vectorstore: ChromaDB vector store instance
            documents: Original documents for BM25 indexing
        """
        self.vectorstore = vectorstore
        self.documents = documents or []
        self.bm25 = None
        self.tokenized_docs = []
        
        if documents:
            self._build_bm25_index(documents)
    
    def _build_bm25_index(self, documents: List[Document]):
        """Build BM25 index from documents"""
        self.documents = documents
        # Tokenize documents for BM25
        self.tokenized_docs = [
            self._tokenize(doc.page_content) for doc in documents
        ]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        print(f"[OK] Built BM25 index with {len(documents)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - lowercase and split on whitespace/punctuation"""
        import re
        # Remove special characters and lowercase
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def semantic_search(self, query: str, k: int = 10, filter_dict: dict = None) -> List[Tuple[Document, float]]:
        """
        Perform semantic search using embeddings
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Optional metadata filter
        
        Returns:
            List of (document, score) tuples
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k, filter=filter_dict)
            # Normalize scores (ChromaDB returns distance, lower is better)
            # Convert to similarity score (higher is better)
            normalized = []
            for doc, score in results:
                # ChromaDB uses L2 distance, convert to similarity
                similarity = 1 / (1 + score)
                normalized.append((doc, similarity))
            return normalized
        except Exception as e:
            print(f"[ERROR] Semantic search failed: {e}")
            return []
    
    def bm25_search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """
        Perform BM25 keyword search
        
        Returns:
            List of (document, score) tuples
        """
        if self.bm25 is None or not self.documents:
            return []
        
        try:
            tokenized_query = self._tokenize(query)
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include docs with positive scores
                    results.append((self.documents[idx], float(scores[idx])))
            
            # Normalize scores to 0-1 range
            if results:
                max_score = max(score for _, score in results)
                if max_score > 0:
                    results = [(doc, score/max_score) for doc, score in results]
            
            return results
        except Exception as e:
            print(f"[ERROR] BM25 search failed: {e}")
            return []
    
    def hybrid_search(
        self, 
        query: str, 
        k: int = 5,
        semantic_weight: float = 0.6,
        bm25_weight: float = 0.4
    ) -> List[Tuple[Document, float]]:
        """
        Perform hybrid search combining semantic and BM25
        Uses Reciprocal Rank Fusion (RRF) for combining results
        
        Args:
            query: Search query
            k: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
            bm25_weight: Weight for BM25 search (0-1)
            
        Returns:
            List of (document, combined_score) tuples
        """
        # Get more candidates for fusion
        candidates_k = k * 3
        
        # Get results from both methods
        semantic_results = self.semantic_search(query, k=candidates_k)
        bm25_results = self.bm25_search(query, k=candidates_k)
        
        # If no BM25 available, use semantic only
        if not bm25_results:
            return semantic_results[:k]
        
        # Reciprocal Rank Fusion (RRF)
        # RRF score = 1 / (rank + constant)
        rrf_constant = 60  # Commonly used constant
        
        # Calculate RRF scores
        doc_scores: Dict[str, float] = {}
        doc_objects: Dict[str, Document] = {}
        
        # Add semantic results with weighted RRF
        for rank, (doc, score) in enumerate(semantic_results):
            doc_id = self._get_doc_id(doc)
            rrf_score = semantic_weight * (1 / (rank + rrf_constant))
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
            doc_objects[doc_id] = doc
        
        # Add BM25 results with weighted RRF
        for rank, (doc, score) in enumerate(bm25_results):
            doc_id = self._get_doc_id(doc)
            rrf_score = bm25_weight * (1 / (rank + rrf_constant))
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_objects:
                doc_objects[doc_id] = doc
        
        # Sort by combined score
        sorted_docs = sorted(
            [(doc_objects[doc_id], score) for doc_id, score in doc_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_docs[:k]
    
    def _get_doc_id(self, doc: Document) -> str:
        """Generate a unique ID for a document"""
        # Use content hash as ID
        content = doc.page_content[:200]  # Use first 200 chars
        source = doc.metadata.get('source', '')
        page = doc.metadata.get('page', '')
        return f"{source}_{page}_{hash(content)}"
    
    def rerank(
        self, 
        query: str, 
        documents: List[Tuple[Document, float]], 
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Simple relevance-based reranking
        Uses keyword matching and document freshness
        
        For production, consider using a cross-encoder model
        """
        reranked = []
        query_tokens = set(self._tokenize(query))
        
        for doc, base_score in documents:
            # Calculate additional relevance factors
            doc_tokens = set(self._tokenize(doc.page_content[:500]))
            
            # Keyword overlap bonus
            overlap = len(query_tokens.intersection(doc_tokens))
            keyword_bonus = min(overlap * 0.02, 0.2)  # Max 20% bonus
            
            # Boost for exact phrase matches
            if query.lower() in doc.page_content.lower():
                keyword_bonus += 0.15
            
            # Final score
            final_score = base_score + keyword_bonus
            reranked.append((doc, final_score))
        
        # Sort by final score
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:top_k]
    
    def search(
        self, 
        query: str, 
        k: int = 5,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        filter_dict: dict = None
    ) -> List[Document]:
        """
        Main search method - performs hybrid search with optional reranking
        Now includes Query Expansion for better recall.
        
        Args:
            query: Search query
            k: Number of results
            use_hybrid: Whether to use hybrid search (vs semantic only)
            use_rerank: Whether to apply reranking
            filter_dict: Optional metadata filter for category filtering
            
        Returns:
            List of relevant documents
        """
        # Step 1: Expand query with legal synonyms for better recall
        expanded_query = expand_query(query)
        if expanded_query != query:
            print(f"[Query Expansion] '{query[:50]}...' -> added legal synonyms")
        
        if use_hybrid and self.bm25 is not None:
            # Use expanded query for BM25 (keyword matching benefits most from expansion)
            # Use original query for semantic (embeddings handle meaning already)
            semantic_results = self.semantic_search(query, k=k*2, filter_dict=filter_dict)
            bm25_results = self.bm25_search(expanded_query, k=k*2)
            
            # If we have a filter, filter BM25 results too
            if filter_dict and bm25_results:
                filtered_bm25 = []
                for doc, score in bm25_results:
                    match = True
                    for key, value in filter_dict.items():
                        if doc.metadata.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_bm25.append((doc, score))
                bm25_results = filtered_bm25
            
            # Combine results using hybrid_search logic
            results = self._combine_results(semantic_results, bm25_results, k=k*2 if use_rerank else k)
        else:
            results = self.semantic_search(query, k=k*2 if use_rerank else k, filter_dict=filter_dict)
        
        if use_rerank and results:
            # Rerank using original query (not expanded) for precision
            results = self.rerank(query, results, top_k=k)
        
        # Return just documents (without scores)
        return [doc for doc, score in results[:k]]
    
    def _combine_results(self, semantic_results, bm25_results, k: int):
        """Combine semantic and BM25 results using RRF"""
        rrf_constant = 60
        doc_scores = {}
        doc_objects = {}
        
        for rank, (doc, score) in enumerate(semantic_results):
            doc_id = self._get_doc_id(doc)
            rrf_score = 0.6 * (1 / (rank + rrf_constant))
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
            doc_objects[doc_id] = doc
        
        for rank, (doc, score) in enumerate(bm25_results):
            doc_id = self._get_doc_id(doc)
            rrf_score = 0.4 * (1 / (rank + rrf_constant))
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_objects:
                doc_objects[doc_id] = doc
        
        sorted_docs = sorted(
            [(doc_objects[doc_id], score) for doc_id, score in doc_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_docs[:k]
    
    def search_with_scores(
        self, 
        query: str, 
        k: int = 5,
        use_hybrid: bool = True,
        use_rerank: bool = True
    ) -> List[Tuple[Document, float]]:
        """
        Search and return documents with scores
        """
        if use_hybrid and self.bm25 is not None:
            results = self.hybrid_search(query, k=k*2 if use_rerank else k)
        else:
            results = self.semantic_search(query, k=k*2 if use_rerank else k)
        
        if use_rerank and results:
            results = self.rerank(query, results, top_k=k)
        
        return results[:k]


def build_bm25_from_vectorstore(vectorstore) -> List[Document]:
    """
    Extract documents from ChromaDB to build BM25 index
    """
    try:
        # Get all documents from ChromaDB
        collection = vectorstore._collection
        results = collection.get(include=['documents', 'metadatas'])
        
        documents = []
        for i, content in enumerate(results['documents']):
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        print(f"[OK] Extracted {len(documents)} documents from vector store")
        return documents
    except Exception as e:
        print(f"[ERROR] Failed to extract documents: {e}")
        return []
