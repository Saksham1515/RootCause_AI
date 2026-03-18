"""
Embedding utilities for semantic search
"""
import os
import numpy as np
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Manages embeddings and FAISS index"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = 384
        self.index = None
        self.metadata = []  # Store metadata for each embedding
        self.chunk_to_id = {}  # Map chunk IDs to metadata

    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def create_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Create FAISS index from embeddings"""
        try:
            if embeddings.shape[1] != self.dimension:
                raise ValueError(f"Expected {self.dimension} dimensions, got {embeddings.shape[1]}")
            index = faiss.IndexFlatL2(self.dimension)
            index.add(embeddings.astype(np.float32))
            self.index = index
            return index
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def search(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Search similar embeddings"""
        if self.index is None:
            logger.warning("Index not initialized")
            return []

        try:
            query_embedding = self.embed([query])[0]
            distances, indices = self.index.search(
                np.array([query_embedding]).astype(np.float32), k
            )
            results = [(idx, dist) for idx, dist in zip(indices[0], distances[0])]
            return results
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            raise

    def save_index(self, path: str):
        """Save index and metadata to disk"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            # Save index
            faiss.write_index(self.index, f"{path}/faiss_index.bin")

            # Save metadata
            metadata_path = f"{path}/metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f)

            logger.info(f"Index saved to {path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

    def load_index(self, path: str):
        """Load index and metadata from disk"""
        try:
            index_path = f"{path}/faiss_index.bin"
            metadata_path = f"{path}/metadata.json"

            self.index = faiss.read_index(index_path)

            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)

            logger.info(f"Index loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise

    def add_metadata(self, chunk_id: str, metadata: Dict):
        """Add metadata for a chunk"""
        self.metadata.append({"chunk_id": chunk_id, **metadata})
        self.chunk_to_id[chunk_id] = len(self.metadata) - 1

    def get_metadata(self, idx: int) -> Optional[Dict]:
        """Get metadata by index"""
        if 0 <= idx < len(self.metadata):
            return self.metadata[idx]
        return None
