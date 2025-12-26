import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict, Any
import streamlit as st
from config.settings import settings
from utils.embeddings import embedding_manager

class VectorStore:
    """FAISS-based vector store for similarity search"""
    
    def __init__(self):
        self.index = None
        self.documents = []
        self.metadata = []
        self.dimension = None
        self.index_path = settings.FAISS_INDEX_PATH
        self.metadata_path = f"{settings.FAISS_INDEX_PATH}.metadata"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Try to load existing index
        self.load_index()
    
    def _initialize_index(self, dimension: int):
        """Initialize FAISS index with given dimension"""
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
    
    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        """Add documents to the vector store"""
        if not texts:
            return
        
        try:
            # Generate embeddings
            embeddings = embedding_manager.embed_texts(texts)
            
            # Initialize index if needed
            if self.index is None:
                self._initialize_index(embeddings.shape[1])
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to index
            self.index.add(embeddings.astype('float32'))
            
            # Store documents and metadata
            self.documents.extend(texts)
            if metadata:
                self.metadata.extend(metadata)
            else:
                self.metadata.extend([{"index": len(self.documents) + i} for i in range(len(texts))])
            
            st.success(f"Added {len(texts)} documents to vector store")
            
        except Exception as e:
            st.error(f"Failed to add documents: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar documents"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        try:
            # Generate query embedding
            query_embedding = embedding_manager.embed_text(query)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            
            # Search
            scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append((
                        self.documents[idx],
                        float(score),
                        self.metadata[idx] if idx < len(self.metadata) else {}
                    ))
            
            return results
            
        except Exception as e:
            st.error(f"Search failed: {e}")
            return []
    
    def save_index(self):
        """Save the FAISS index and metadata to disk"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
                
                # Save metadata
                with open(self.metadata_path, 'wb') as f:
                    pickle.dump({
                        'documents': self.documents,
                        'metadata': self.metadata,
                        'dimension': self.dimension
                    }, f)
                
                st.success("Vector store saved successfully")
                
        except Exception as e:
            st.error(f"Failed to save vector store: {e}")
    
    def load_index(self):
        """Load the FAISS index and metadata from disk"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                # Load index
                self.index = faiss.read_index(self.index_path)
                
                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.metadata = data['metadata']
                    self.dimension = data['dimension']
                
                st.info(f"Loaded vector store with {len(self.documents)} documents")
                
        except Exception as e:
            st.warning(f"Could not load existing vector store: {e}")
    
    def clear(self):
        """Clear all documents from the vector store"""
        self.index = None
        self.documents = []
        self.metadata = []
        self.dimension = None
        
        # Remove files
        for path in [self.index_path, self.metadata_path]:
            if os.path.exists(path):
                os.remove(path)
        
        st.success("Vector store cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_exists": self.index is not None
        }

# Global vector store instance
vector_store = VectorStore()
