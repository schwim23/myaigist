from .openai_client import get_openai_client

class Embedder:
    """Agent for creating embeddings"""

    def __init__(self):
        self.client = get_openai_client()
        self.model = "text-embedding-3-large"
