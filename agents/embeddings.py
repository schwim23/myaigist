import os
from typing import List, Optional
from .openai_client import get_openai_client

class Embedder:
    """Agent for creating embeddings"""

    def __init__(self):
        self.client = get_openai_client()
        self.model = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-large')
        print(f"✅ Embedder initialized with model: {self.model}")
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        Create embedding for a single text
        
        Args:
            text (str): Text to embed
            
        Returns:
            Optional[List[float]]: Embedding vector or None if failed
        """
        try:
            if not text or len(text.strip()) == 0:
                print("⚠️  Empty text provided for embedding")
                return None
            
            # Clean text
            text = text.strip()
            
            # Create embedding
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            # Extract embedding
            embedding = response.data[0].embedding
            
            print(f"✅ Created embedding for text ({len(text)} chars) -> {len(embedding)} dims")
            return embedding
            
        except Exception as e:
            print(f"❌ Error creating embedding: {e}")
            return None
    
    def create_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Create embeddings for multiple texts in a batch
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            List[Optional[List[float]]]: List of embedding vectors
        """
        try:
            if not texts:
                return []
            
            # Filter out empty texts but keep track of indices
            valid_texts = []
            text_indices = []
            
            for i, text in enumerate(texts):
                if text and len(text.strip()) > 0:
                    valid_texts.append(text.strip())
                    text_indices.append(i)
            
            if not valid_texts:
                print("⚠️  No valid texts for batch embedding")
                return [None] * len(texts)
            
            # Create batch embeddings
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            
            # Prepare results array
            results = [None] * len(texts)
            
            # Fill in results for valid texts
            for i, embedding_data in enumerate(response.data):
                original_index = text_indices[i]
                results[original_index] = embedding_data.embedding
            
            print(f"✅ Created {len(valid_texts)} embeddings from {len(texts)} texts")
            return results
            
        except Exception as e:
            print(f"❌ Error creating batch embeddings: {e}")
            return [None] * len(texts)
