"""
Audio transcription and text-to-speech agent - Updated for WebM support
"""
import os
import uuid
import tempfile
import subprocess
from openai import OpenAI

class Transcriber:
    """Agent responsible for audio transcription and text-to-speech"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.audio_dir = 'static/audio'
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text using Whisper
        Handles WebM files by converting them first
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            # Check if file is WebM (common for browser recordings)
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            
            if file_ext == '.webm':
                # Convert WebM to MP3 for Whisper compatibility
                converted_path = self._convert_webm_to_mp3(audio_file_path)
                transcription_file = converted_path
            else:
                transcription_file = audio_file_path
            
            # Transcribe with Whisper
            with open(transcription_file, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Clean up converted file if we created one
            if file_ext == '.webm' and os.path.exists(converted_path):
                os.remove(converted_path)
                
            return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            
        except Exception as e:
            print(f"Transcription error: {e}")
            raise RuntimeError(f"Error transcribing audio: {str(e)}")
    
    def _convert_webm_to_mp3(self, webm_path: str) -> str:
        """
        Convert WebM audio to MP3 using ffmpeg
        Falls back to direct upload if ffmpeg not available
        """
        try:
            # Create temporary MP3 file
            temp_mp3 = os.path.join(
                os.path.dirname(webm_path), 
                f"temp_{uuid.uuid4().hex}.mp3"
            )
            
            # Try to use ffmpeg for conversion
            try:
                result = subprocess.run([
                    'ffmpeg', '-i', webm_path, 
                    '-acodec', 'mp3', 
                    '-ar', '16000',  # Sample rate for Whisper
                    '-ac', '1',      # Mono
                    '-y',           # Overwrite output
                    temp_mp3
                ], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
                
                if result.returncode == 0 and os.path.exists(temp_mp3):
                    print(f"✅ Successfully converted WebM to MP3")
                    return temp_mp3
                else:
                    print(f"⚠️ ffmpeg failed: {result.stderr}")
                    raise subprocess.CalledProcessError(result.returncode, 'ffmpeg')
                    
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️ ffmpeg not available, trying direct WebM upload")
                # If ffmpeg fails, try uploading WebM directly
                return webm_path
                
        except Exception as e:
            print(f"⚠️ Conversion error: {e}, using original file")
            return webm_path
    
    def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            
        Returns:
            URL path to generated audio file
        """
        try:
            # Truncate text if too long
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text,
                response_format="mp3"
            )
            
            # Save audio file
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(self.audio_dir, audio_filename)
            
            # Write the audio content to file
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            # Return URL path
            return f"/static/audio/{audio_filename}"
            
        except Exception as e:
            print(f"TTS error: {e}")
            raise RuntimeError(f"Error generating speech: {str(e)}")