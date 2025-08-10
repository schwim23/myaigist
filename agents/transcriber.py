import os
import tempfile
import uuid
from pathlib import Path
from openai import OpenAI
from typing import Optional

class Transcriber:
    """Agent responsible for audio transcription and text-to-speech"""
    
    def __init__(self):
        """Initialize the Transcriber with OpenAI client"""
        try:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.audio_dir = Path('static/audio')
            self.audio_dir.mkdir(exist_ok=True)
            
            # Supported audio formats for transcription
            self.supported_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
            
            print("✅ Transcriber initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Transcriber: {e}")
            raise
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using OpenAI Whisper
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            print(f"🎤 Transcribing audio file: {audio_file_path}")
            
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Check file size (OpenAI has a 25MB limit)
            file_size = os.path.getsize(audio_file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB
                raise ValueError("Audio file too large. Maximum size is 25MB.")
            
            # Check if file extension is supported
            file_ext = Path(audio_file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                print(f"⚠️  Unsupported format {file_ext}, attempting transcription anyway...")
            
            # Transcribe using OpenAI Whisper
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Handle both string and object responses
            if hasattr(transcript, 'text'):
                transcribed_text = transcript.text
            else:
                transcribed_text = str(transcript)
            
            print(f"✅ Successfully transcribed audio: {len(transcribed_text)} characters")
            return transcribed_text.strip()
            
        except Exception as e:
            error_msg = f"Error transcribing audio: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def text_to_speech(self, text: str, voice: str = "nova") -> Optional[str]:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text (str): Text to convert to speech
            voice (str): Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Optional[str]: URL path to generated audio file, or None if failed
        """
        try:
            if not text or len(text.strip()) == 0:
                print("⚠️  No text provided for TTS")
                return None
            
            # Limit text length for TTS (OpenAI has a 4096 character limit)
            if len(text) > 4000:
                text = text[:4000] + "..."
                print("⚠️  Text truncated for TTS (4000 char limit)")
            
            print(f"🔊 Generating speech for {len(text)} characters")
            
            # Generate unique filename
            audio_id = str(uuid.uuid4())
            audio_filename = f"speech_{audio_id}.mp3"
            audio_path = self.audio_dir / audio_filename
            
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            # Save audio file
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            # Return URL path for the frontend
            audio_url = f"/static/audio/{audio_filename}"
            print(f"✅ Generated speech audio: {audio_url}")
            return audio_url
            
        except Exception as e:
            print(f"❌ Error generating speech: {e}")
            return None
    
    def transcribe(self, audio_file) -> str:
        """
        Transcribe uploaded file object (Flask file upload)
        
        Args:
            audio_file: Flask uploaded file object
            
        Returns:
            str: Transcribed text
        """
        try:
            # Save uploaded file temporarily
            temp_dir = tempfile.gettempdir()
            temp_filename = f"temp_audio_{uuid.uuid4()}{Path(audio_file.filename).suffix}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Save the uploaded file
            audio_file.save(temp_path)
            
            try:
                # Transcribe the temporary file
                result = self.transcribe_audio(temp_path)
                return result
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            error_msg = f"Error transcribing uploaded file: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old audio files to save disk space
        
        Args:
            max_age_hours (int): Maximum age of files to keep in hours
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for audio_file in self.audio_dir.glob("*.mp3"):
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > max_age_seconds:
                    audio_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                print(f"🧹 Cleaned up {cleaned_count} old audio files")
                
        except Exception as e:
            print(f"⚠️  Error cleaning up audio files: {e}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return self.supported_formats.copy()
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]