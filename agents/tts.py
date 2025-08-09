from .openai_client import get_openai_client

class TextToSpeech:
    """Agent for text-to-speech"""

    def __init__(self):
        self.client = get_openai_client()
        self.model = "gpt-4o-mini-tts"
