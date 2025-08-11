import os
from openai import OpenAI
from typing import List, Dict, Any
import re
from .vector_store import VectorStore

class QAAgent:
    """Agent responsible for question answering using RAG approach"""
    
    def __init__(self):
        """Initialize the QA Agent"""
        try:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
            
            # Storage for documents and their metadata
            self.documents = []  # List of {'text': str, 'title': str, 'chunks': List[str]}
            
            # Initialize vector store for embeddings
            self.vector_store = VectorStore()
            
            print("✅ QAAgent initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing QAAgent: {e}")
            raise
    
    def add_document(self, text: str, title: str = "Document") -> bool:
        """
        Add a document to the knowledge base
        
        Args:
            text (str): Document text
            title (str): Document title
            
        Returns:
            bool: Success status
        """
        try:
            if not text or len(text.strip()) < 10:
                print("⚠️  Document too short to add")
                return False
            
            # Clean and chunk the text
            cleaned_text = self._clean_text(text)
            chunks = self._chunk_text(cleaned_text)
            
            if not chunks:
                print("⚠️  No chunks created from document")
                return False
            
            # Store document
            doc_index = len(self.documents)
            document = {
                'text': cleaned_text,
                'title': title,
                'chunks': chunks
            }
            self.documents.append(document)
            
            # Add chunks to vector store
            for chunk_index, chunk in enumerate(chunks):
                metadata = {
                    'doc_index': doc_index,
                    'chunk_index': chunk_index,
                    'title': title,
                    'doc_title': title
                }
                self.vector_store.add_text(chunk, metadata)
            
            # Save vector store
            self.vector_store.save()
            
            print(f"✅ Added document '{title}' with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            return False
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question using the stored documents
        
        Args:
            question (str): User question
            
        Returns:
            str: Generated answer
        """
        try:
            if not question or len(question.strip()) < 3:
                return "Please provide a valid question."
            
            # Check if we have vectors (this is the real indicator of available content)
            if not self.vector_store.vectors:
                return "No documents have been uploaded yet. Please upload a document first, then ask your question."
            
            print(f"❓ Processing question: {question}")
            print(f"📚 Available documents: {len(self.documents)}")
            print(f"📄 Available chunks: {len(self.vector_store.vectors)}")
            
            # Get relevant context
            relevant_context = self._get_relevant_context(question)
            
            if not relevant_context:
                return "I couldn't find relevant information in the uploaded documents to answer your question."
            
            # Generate answer using OpenAI
            answer = self._generate_answer(question, relevant_context)
            
            print(f"✅ Generated answer for question")
            return answer
            
        except Exception as e:
            error_msg = f"Error answering question: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text (str): Text to chunk
            chunk_size (int): Size of each chunk
            overlap (int): Overlap between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending within last 100 chars
                for i in range(min(100, chunk_size)):
                    if text[end - i - 1] in '.!?':
                        end = end - i
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _get_vector_stats(self):
        """Get vector store statistics"""
        stats = self.vector_store.get_stats()
        print(f"📊 Vector Store Stats: {stats['total_vectors']} vectors, {stats['dimension']} dims, {stats['memory_usage_mb']:.1f}MB")
    
    def _get_relevant_context(self, question: str, top_k: int = 3) -> str:
        """
        Get most relevant text chunks for the question using embedding search
        
        Args:
            question (str): User question
            top_k (int): Number of top chunks to return
            
        Returns:
            str: Combined relevant context
        """
        try:
            if not self.vector_store.vectors:
                # Fallback: return first part of most recent document
                if self.documents:
                    latest_doc = self.documents[-1]
                    print(f"🔄 Using fallback context from: {latest_doc['title']}")
                    return latest_doc['text'][:2000]
                return ""
            
            print(f"🔍 Searching among {len(self.vector_store.vectors)} chunks for: '{question}'")
            
            # Use vector store similarity search
            search_results = self.vector_store.similarity_search(
                query=question,
                top_k=top_k,
                min_similarity=0.1  # Lower threshold for better matching
            )
            
            if not search_results:
                print("⚠️  No similar chunks found, trying with lower threshold")
                search_results = self.vector_store.similarity_search(
                    query=question,
                    top_k=top_k,
                    min_similarity=0.0  # Try with no threshold
                )
            
            relevant_chunks = []
            for i, result in enumerate(search_results):
                similarity_score = result['similarity']
                metadata = result['metadata']
                chunk_text = metadata['text']
                
                print(f"  🎯 Chunk {i+1}: similarity={similarity_score:.3f}")
                
                # Show preview of matched chunk
                preview = chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
                print(f"    📝 Matched chunk: {preview}")
                
                relevant_chunks.append(f"[From: {metadata['title']}]\n{chunk_text}")
            
            if not relevant_chunks:
                # Ultimate fallback to most recent document
                print("⚠️  No chunks found, using fallback")
                if self.documents:
                    latest_doc = self.documents[-1]
                    return latest_doc['text'][:2000]
                return ""
            
            context = "\n\n---\n\n".join(relevant_chunks)
            print(f"✅ Final context length: {len(context)} characters from {len(relevant_chunks)} chunks")
            
            return context
            
        except Exception as e:
            print(f"❌ Error getting relevant context: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to most recent document
            if self.documents:
                latest_doc = self.documents[-1]
                print(f"🔄 Using fallback - latest document: {latest_doc['title']}")
                return latest_doc['text'][:2000]
            return ""
    
    
    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using OpenAI with the provided context
        
        Args:
            question (str): User question
            context (str): Relevant context
            
        Returns:
            str: Generated answer
        """
        system_prompt = """You are a helpful AI assistant that answers questions based on provided context.

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the context
2. If the answer isn't clearly in the context, say so honestly
3. Be specific and cite relevant parts when possible
4. Keep answers concise but complete
5. If context contains multiple sources, you can reference them

Format your response naturally and conversationally."""

        user_prompt = f"""Context:
{context}

Question: {question}

Please answer the question based on the context provided above."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the QA agent"""
        vector_stats = self.vector_store.get_stats()
        
        # Count unique documents from vector metadata if documents list is empty
        unique_docs = set()
        if self.vector_store.metadata:
            for metadata in self.vector_store.metadata:
                if 'title' in metadata:
                    unique_docs.add(metadata['title'])
        
        # Use in-memory count if available, otherwise count from vectors
        doc_count = len(self.documents) if self.documents else len(unique_docs)
        
        return {
            'documents_count': doc_count,
            'chunks_count': vector_stats['total_vectors'],
            'vectors_ready': vector_stats['total_vectors'] > 0,
            'ready_for_questions': vector_stats['total_vectors'] > 0,
            'embedding_dimension': vector_stats['dimension'],
            'memory_usage_mb': vector_stats['memory_usage_mb']
        }
    
    def clear_documents(self):
        """Clear all stored documents"""
        self.documents = []
        self.vector_store.clear()
        self.vector_store.save()  # Save cleared state
        print("🗑️  Cleared all documents and vectors")