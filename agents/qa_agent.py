"""
Q&A agent with RAG (Retrieval Augmented Generation) - Python 3.13 Compatible
Uses scikit-learn instead of faiss for vector similarity search
"""
import os
import numpy as np
from typing import List, Dict
from openai import OpenAI
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity

class QAAgent:
    """Agent responsible for question answering using RAG"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-3.5-turbo"
        self.embedding_model = "text-embedding-3-small"
        
        # Document storage
        self.documents = []
        self.embeddings = []
        self.document_metadata = []
        
        # Initialize tokenizer
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def add_document(self, text: str, title: str = "Document"):
        """
        Add a document to the knowledge base
        
        Args:
            text: Document text content
            title: Document title/name
        """
        try:
            # Clear previous documents (for simplicity)
            self.documents = []
            self.embeddings = []
            self.document_metadata = []
            
            # Split text into chunks for better retrieval
            chunks = self._chunk_text(text)
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self._get_embedding(chunk)
                
                # Store document chunk
                self.documents.append(chunk)
                self.embeddings.append(embedding)
                self.document_metadata.append({
                    'title': title,
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                })
            
            print(f"Added {len(chunks)} chunks from '{title}' to knowledge base")
            
        except Exception as e:
            raise RuntimeError(f"Error adding document: {str(e)}")
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question based on stored documents
        
        Args:
            question: User's question
            
        Returns:
            Generated answer
        """
        if not self.documents:
            raise RuntimeError("No documents available. Please upload content first.")
        
        try:
            # Find relevant document chunks
            relevant_chunks = self._find_relevant_chunks(question, top_k=3)
            
            # Build context from relevant chunks
            context = "\n\n".join([chunk['content'] for chunk in relevant_chunks])
            
            # Generate answer
            prompt = f"""Based on the following context, please answer the question accurately and comprehensively.

Context:
{context}

Question: {question}

Answer:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Add source information
            sources = set([chunk['metadata']['title'] for chunk in relevant_chunks])
            if len(sources) == 1:
                answer += f"\n\n*Source: {list(sources)[0]}*"
            else:
                answer += f"\n\n*Sources: {', '.join(sources)}*"
            
            return answer
            
        except Exception as e:
            raise RuntimeError(f"Error answering question: {str(e)}")
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into smaller chunks for better retrieval"""
        # Split by sentences first
        sentences = text.replace('\n', ' ').split('. ')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence exceeds chunk size
            test_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            
            if len(self.tokenizer.encode(test_chunk)) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:2000]]  # Fallback for very long text
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Error generating embedding: {str(e)}")
    
    def _find_relevant_chunks(self, question: str, top_k: int = 3) -> List[Dict]:
        """Find most relevant document chunks for a question using scikit-learn"""
        if not self.embeddings:
            return []
        
        try:
            # Get question embedding
            question_embedding = self._get_embedding(question)
            
            # Convert to numpy arrays for scikit-learn
            question_array = np.array(question_embedding).reshape(1, -1)
            embeddings_array = np.array(self.embeddings)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(question_array, embeddings_array)[0]
            
            # Get top k most similar chunks
            top_indices = np.argsort(similarities)[-top_k:][::-1]  # Reverse for descending order
            
            relevant_chunks = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    relevant_chunks.append({
                        'index': idx,
                        'similarity': float(similarities[idx]),
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx]
                    })
            
            return relevant_chunks
            
        except Exception as e:
            print(f"Error in similarity search: {e}")
            # Fallback: return first few chunks
            return [
                {
                    'index': i,
                    'similarity': 0.5,
                    'content': self.documents[i],
                    'metadata': self.document_metadata[i]
                }
                for i in range(min(top_k, len(self.documents)))
            ]