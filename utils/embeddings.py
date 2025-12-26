from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import streamlit as st
from config.settings import settings

class EmbeddingManager:
    """Manages embedding models and operations"""
    
    def __init__(self):
        self._model = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Get or create embedding model instance"""
        if self._model is None:
            try:
                with st.spinner("Loading embedding model..."):
                    self._model = SentenceTransformer(
                        settings.EMBEDDING_MODEL,
                        device=settings.EMBEDDING_DEVICE
                    )
            except Exception as e:
                st.error(f"Failed to load embedding model: {e}")
                raise
        return self._model
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            st.error(f"Failed to generate embeddings: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()

# Global embedding manager instance
embedding_manager = EmbeddingManager()
