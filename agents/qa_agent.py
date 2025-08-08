"""
Q&A Agent for answering questions using RAG (Retrieval-Augmented Generation)
"""

import os
import numpy as np
from typing import List, Dict
from openai import OpenAI

try:
    import tiktoken
except ImportError:
    tiktoken = None

from sklearn.metrics.pairwise import cosine_similarity

class QAAgent:
    def __init__(self, api_key: str):
        """Initialize the Q&A agent with OpenAI API key"""
        self.client = OpenAI(api_key=api_key)
        self.documents = []
        self.embeddings = []
        self.model = "gpt-3.5-turbo"
        self.embedding_model = "text-embedding-ada-002"
        
        # Initialize tokenizer if available
        if tiktoken is not None:
            try:
                self.tokenizer = tiktoken.encoding_for_model(self.model)
            except Exception as e:
                print(f"Warning: Could not initialize tiktoken: {e}")
                self.tokenizer = None
        else:
            self.tokenizer = None
            print("Warning: tiktoken not available, using simple token estimation")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text, with fallback for when tiktoken is unavailable"""
        if self.tokenizer is not None:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Simple fallback: approximately 4 characters per token
        return len(text) // 4
    
    def chunk_text(self, text: str, max_tokens: int = 500) -> List[str]:
        """Split text into chunks that fit within token limits"""
        if not text:
            return []
        
        # Simple chunking by sentences if tiktoken unavailable
        if self.tokenizer is None:
            sentences = text.split('. ')
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                test_chunk = current_chunk + sentence + ". "
                if self.count_tokens(test_chunk) > max_tokens and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
                else:
                    current_chunk = test_chunk
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Use tiktoken for precise chunking if available
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0.0] * 1536  # Default embedding dimension
    
    def add_document(self, content: str, metadata: Dict = None):
        """Add a document to the knowledge base"""
        if not content:
            return
        
        # Split into chunks
        chunks = self.chunk_text(content)
        
        for chunk in chunks:
            if chunk.strip():
                # Get embedding
                embedding = self.get_embedding(chunk)
                
                # Store document and embedding
                doc_data = {
                    'content': chunk,
                    'metadata': metadata or {}
                }
                self.documents.append(doc_data)
                self.embeddings.append(embedding)
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar documents using cosine similarity"""
        if not self.documents:
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Calculate similarities
        similarities = cosine_similarity(
            [query_embedding], 
            self.embeddings
        )[0]
        
        # Get top-k most similar documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'content': self.documents[idx]['content'],
                'metadata': self.documents[idx]['metadata'],
                'similarity': similarities[idx]
            })
        
        return results
    
    def answer_question(self, question: str, context_docs: List[str] = None) -> str:
        """Answer a question using RAG approach"""
        try:
            # If no context provided, search for relevant documents
            if context_docs is None:
                similar_docs = self.search_similar(question, top_k=3)
                context_docs = [doc['content'] for doc in similar_docs]
            
            # Prepare context
            context = "\n\n".join(context_docs[:3])  # Limit context length
            
            # Limit context to prevent token overflow
            max_context_tokens = 2000
            if self.count_tokens(context) > max_context_tokens:
                # Truncate context if too long
                context = context[:max_context_tokens * 4]  # Rough character limit
            
            # Create prompt
            prompt = f"""Based on the following context, please answer the question. If the answer is not in the context, say so clearly.

Context:
{context}

Question: {question}

Answer:"""
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
    def clear_documents(self):
        """Clear all stored documents"""
        self.documents = []
        self.embeddings = []
    
    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        return {
            'document_count': len(self.documents),
            'total_tokens': sum(self.count_tokens(doc['content']) for doc in self.documents),
            'has_tiktoken': tiktoken is not None
        }
