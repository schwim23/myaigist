"""
Text summarization agent using OpenAI - Updated with Three Detail Levels
"""
import os
from openai import OpenAI

class Summarizer:
    """Agent responsible for text summarization with multiple detail levels"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-3.5-turbo"
    
    def summarize(self, text: str, detail_level: str = "standard") -> str:
        """
        Generate a summary with specified detail level
        
        Args:
            text: Text to summarize
            detail_level: "quick", "standard", or "detailed"
            
        Returns:
            Generated summary
        """
        if not text.strip():
            raise ValueError("No text provided for summarization")
        
        # Truncate text if too long (GPT has token limits)
        max_input_length = {
            "quick": 8000,
            "standard": 12000,
            "detailed": 16000
        }
        
        input_length = max_input_length.get(detail_level.lower(), 12000)
        if len(text) > input_length:
            text = text[:input_length] + "..."
        
        # Get the appropriate prompt and settings
        prompt, max_tokens, temperature = self._get_prompt_settings(text, detail_level.lower())
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            raise RuntimeError(f"Error generating summary: {str(e)}")
    
    def _get_prompt_settings(self, text: str, detail_level: str) -> tuple:
        """Get prompt, max_tokens, and temperature based on detail level"""
        
        if detail_level == "quick":
            prompt = f"""Provide a concise summary of the following text in 2-3 key bullet points. Focus only on the most essential information and main conclusions.

Text:
{text}

Quick Summary (2-3 bullet points):
•"""
            return prompt, 300, 0.2
            
        elif detail_level == "detailed":
            prompt = f"""Provide a comprehensive and detailed summary of the following text. Include:

1. **Main Topic & Context**: What is this about and why is it important?
2. **Key Points**: 5-7 detailed bullet points covering all major themes
3. **Important Details**: Specific facts, numbers, dates, or examples mentioned
4. **Analysis & Insights**: What patterns, trends, or implications emerge?
5. **Conclusions**: What are the main takeaways and outcomes?
6. **Additional Context**: Any background information or related topics mentioned

Make sure to capture nuances and provide depth while remaining well-organized.

Text:
{text}

Detailed Summary:"""
            return prompt, 1200, 0.3
            
        else:  # standard (default)
            prompt = f"""Provide a well-structured summary of the following text that covers the main points comprehensively but concisely. Include:

• **Main Topic**: What this content is about
• **Key Points**: 4-5 important points or themes (use bullet points)  
• **Important Details**: Relevant facts, numbers, or examples
• **Conclusions**: Main takeaways or outcomes

Keep it informative but readable - not too brief, not too lengthy.

Text:
{text}

Summary:"""
            return prompt, 600, 0.3