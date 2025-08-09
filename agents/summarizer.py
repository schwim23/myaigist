from .openai_client import get_openai_client

class Summarizer:
    """Agent responsible for text summarization with multiple detail levels"""

    def __init__(self):
        self.client = get_openai_client()
        self.model = "gpt-3.5-turbo"
