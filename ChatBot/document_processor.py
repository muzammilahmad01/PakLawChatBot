"""
Document Processor for RAG Pipeline
Handles PDF loading, text extraction, and chunking for vector storage
"""

import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentProcessor:
    """Process PDF documents for RAG pipeline"""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks for splitting (1500 optimal for legal docs)
            chunk_overlap: Overlap between chunks to maintain context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """
        Load a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of Document objects with metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Add source filename to metadata
            for doc in documents:
                doc.metadata['source'] = os.path.basename(pdf_path)
                doc.metadata['full_path'] = pdf_path
            
            print(f"[OK] Loaded {len(documents)} pages from {os.path.basename(pdf_path)}")
            return documents
            
        except Exception as e:
            print(f"[ERROR] loading {pdf_path}: {str(e)}")
            return []
    
    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Document]:
        """
        Load all PDFs from a directory
        
        Args:
            directory_path: Path to directory containing PDFs
            recursive: Whether to search subdirectories
            
        Returns:
            List of all Document objects from all PDFs
        """
        all_documents = []
        pdf_count = 0
        
        if recursive:
            # Walk through all subdirectories
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_path = os.path.join(root, file)
                        docs = self.load_pdf(pdf_path)
                        all_documents.extend(docs)
                        if docs:
                            pdf_count += 1
        else:
            # Only check immediate directory
            for file in os.listdir(directory_path):
                if file.lower().endswith('.pdf'):
                    pdf_path = os.path.join(directory_path, file)
                    docs = self.load_pdf(pdf_path)
                    all_documents.extend(docs)
                    if docs:
                        pdf_count += 1
        
        print(f"\n[OK] Total: Loaded {pdf_count} PDFs with {len(all_documents)} pages")
        return all_documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        
        # Add contextual headers to each chunk
        # This helps the embedding model understand WHAT document the text is from
        for chunk in chunks:
            source = chunk.metadata.get('source', '')
            page = chunk.metadata.get('page', '')
            department = chunk.metadata.get('department', '')
            
            # Build a context header
            header_parts = []
            if department:
                header_parts.append(f"Category: {department.replace('_', ' ')}")
            if source:
                # Clean up source name (remove .pdf extension)
                clean_source = source.replace('.pdf', '').replace('.PDF', '')
                header_parts.append(f"Law: {clean_source}")
            if page != '':
                header_parts.append(f"Page: {page}")
            
            if header_parts:
                header = " | ".join(header_parts)
                chunk.page_content = f"[{header}]\n{chunk.page_content}"
        
        print(f"[OK] Created {len(chunks)} chunks from {len(documents)} pages (with contextual headers)")
        return chunks
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """
        Complete pipeline: Load PDF and chunk it
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of chunked Document objects ready for embedding
        """
        documents = self.load_pdf(pdf_path)
        if not documents:
            return []
        
        chunks = self.chunk_documents(documents)
        return chunks
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> List[Document]:
        """
        Complete pipeline: Load all PDFs from directory and chunk them
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of chunked Document objects ready for embedding
        """
        documents = self.load_directory(directory_path, recursive)
        if not documents:
            return []
        
        chunks = self.chunk_documents(documents)
        return chunks


# Convenience function for quick testing
def process_single_pdf(pdf_path: str) -> List[Document]:
    """Quick function to process a single PDF"""
    processor = DocumentProcessor()
    return processor.process_pdf(pdf_path)


if __name__ == "__main__":
    # Test with Pakistan's Constitution
    test_pdf = "data/test_data/Pakistan's Constituion.pdf"
    
    if os.path.exists(test_pdf):
        print(f"Testing document processor with: {test_pdf}\n")
        chunks = process_single_pdf(test_pdf)
        
        if chunks:
            print(f"\n[OK] Success! Created {len(chunks)} chunks")
            print(f"\nSample chunk:")
            print(f"Content: {chunks[0].page_content[:200]}...")
            print(f"Metadata: {chunks[0].metadata}")
    else:
        print(f"Test PDF not found: {test_pdf}")
