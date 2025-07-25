import os
import pickle
from typing import Dict, Any, List, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

class VectorStoreService:
    def __init__(self, storage_dir: str = "/tmp/vector_store"):
        self.storage_dir = storage_dir
        self.embeddings = OllamaEmbeddings(
            model=os.getenv("TEXT_MODEL", "mistral:7b-instruct"),
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_vector_store_path(self, document_id: str) -> str:
        """Get the file path for a document's vector store"""
        return os.path.join(self.storage_dir, document_id)
    
    def create_vector_store(self, document_id: str, text_content: str) -> bool:
        """Create and store vector embeddings for a document"""
        try:
            # Create document chunks
            docs = [Document(page_content=text_content)]
            splits = self.text_splitter.split_documents(docs)
            
            # Create vector store
            vectorstore = FAISS.from_documents(splits, self.embeddings)
            
            # Save to disk using FAISS save method
            vector_store_path = self._get_vector_store_path(document_id)
            vectorstore.save_local(vector_store_path)
            
            return True
        except Exception as e:
            print(f"Error creating vector store for {document_id}: {e}")
            return False
    
    def load_vector_store(self, document_id: str) -> Optional[FAISS]:
        """Load vector store from disk"""
        try:
            vector_store_path = self._get_vector_store_path(document_id)
            if not os.path.exists(vector_store_path):
                return None
            
            # Load using FAISS load method
            vectorstore = FAISS.load_local(vector_store_path, self.embeddings)
            
            return vectorstore
        except Exception as e:
            print(f"Error loading vector store for {document_id}: {e}")
            return None
    
    def search_similar(self, document_id: str, query: str, k: int = 3) -> List[Document]:
        """Search for similar documents in the vector store"""
        vectorstore = self.load_vector_store(document_id)
        if vectorstore is None:
            return []
        
        try:
            return vectorstore.similarity_search(query, k=k)
        except Exception as e:
            print(f"Error searching vector store for {document_id}: {e}")
            return []
    
    def delete_vector_store(self, document_id: str) -> bool:
        """Delete vector store from disk"""
        try:
            vector_store_path = self._get_vector_store_path(document_id)
            if os.path.exists(vector_store_path):
                os.remove(vector_store_path)
            return True
        except Exception as e:
            print(f"Error deleting vector store for {document_id}: {e}")
            return False
    
    def list_stored_documents(self) -> List[str]:
        """List all document IDs that have stored vector stores"""
        try:
            files = os.listdir(self.storage_dir)
            return [f for f in files if os.path.isdir(os.path.join(self.storage_dir, f))]
        except Exception as e:
            print(f"Error listing stored documents: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored vector databases"""
        try:
            document_ids = self.list_stored_documents()
            total_size = 0
            
            for doc_id in document_ids:
                vector_store_path = self._get_vector_store_path(doc_id)
                if os.path.exists(vector_store_path):
                    total_size += os.path.getsize(vector_store_path)
            
            return {
                "total_documents": len(document_ids),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "document_ids": document_ids
            }
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {"error": str(e)}

# Global instance
vector_store_service = VectorStoreService() 