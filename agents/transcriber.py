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
            
            # Supported audio and video formats for transcription
            self.supported_formats = [
                # Audio formats
                '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.mpga',
                # Video formats (audio will be extracted)
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpeg', '.mpg'
            ]
            
            print("✅ Transcriber initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Transcriber: {e}")
            raise
    
    def transcribe_audio(self, media_file_path: str) -> str:
        """
        Transcribe audio or video file using OpenAI Whisper
        
        Args:
            media_file_path (str): Path to the audio or video file
            
        Returns:
            str: Transcribed text
        """
        try:
            print(f"🎬 Transcribing media file: {media_file_path}")
            
            if not os.path.exists(media_file_path):
                raise FileNotFoundError(f"Media file not found: {media_file_path}")
            
            # Check file size (OpenAI has a 25MB limit)
            file_size = os.path.getsize(media_file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB
                raise ValueError("Media file too large. Maximum size is 25MB.")
            
            # Check if file extension is supported
            file_ext = Path(media_file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                print(f"⚠️  Unsupported format {file_ext}, attempting transcription anyway...")
            
            # Determine if it's audio or video
            video_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpeg', '.mpg']
            is_video = file_ext in video_formats
            
            if is_video:
                print(f"🎥 Processing video file: {file_ext} (audio will be extracted)")
            else:
                print(f"🎵 Processing audio file: {file_ext}")
            
            # Check if we need to convert the format for Whisper
            whisper_supported_formats = ['.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm']
            
            if file_ext not in whisper_supported_formats:
                # Convert unsupported formats (like .mov) to supported format
                print(f"🔄 Converting {file_ext} to .mp4 for Whisper compatibility...")
                import subprocess
                temp_dir = tempfile.gettempdir()
                converted_file = os.path.join(temp_dir, f"converted_{uuid.uuid4()}.mp4")
                
                try:
                    # Use ffmpeg to convert to mp4
                    result = subprocess.run([
                        'ffmpeg', '-i', media_file_path, 
                        '-c:a', 'aac', '-c:v', 'libx264', 
                        '-y', converted_file
                    ], capture_output=True, text=True, check=True)
                    
                    print(f"✅ Successfully converted {file_ext} to .mp4")
                    
                    # Transcribe the converted file
                    with open(converted_file, 'rb') as media_file:
                        transcript = self.client.audio.transcriptions.create(
                            model=os.getenv('OPENAI_WHISPER_MODEL', 'whisper-1'),
                            file=media_file,
                            response_format="text"
                        )
                    
                    # Clean up converted file
                    if os.path.exists(converted_file):
                        os.remove(converted_file)
                        
                except subprocess.CalledProcessError as e:
                    error_msg = f"Failed to convert {file_ext} file: {e.stderr}"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                except Exception as e:
                    # Clean up on any error
                    if os.path.exists(converted_file):
                        os.remove(converted_file)
                    raise e
            else:
                # Direct transcription for supported formats
                with open(media_file_path, 'rb') as media_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=os.getenv('OPENAI_WHISPER_MODEL', 'whisper-1'),
                        file=media_file,
                        response_format="text"
                    )
            
            # Handle both string and object responses
            if hasattr(transcript, 'text'):
                transcribed_text = transcript.text
            else:
                transcribed_text = str(transcript)
            
            media_type = "video" if is_video else "audio"
            print(f"✅ Successfully transcribed {media_type}: {len(transcribed_text)} characters")
            return transcribed_text.strip()
            
        except Exception as e:
            error_msg = f"Error transcribing media: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
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
                model=os.getenv('OPENAI_TTS_MODEL', 'tts-1'),
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
    
    def transcribe(self, media_file) -> str:
        """
        Transcribe uploaded audio/video file object (Flask file upload)
        
        Args:
            media_file: Flask uploaded file object (audio or video)
            
        Returns:
            str: Transcribed text
        """
        try:
            # Save uploaded file temporarily
            temp_dir = tempfile.gettempdir()
            temp_filename = f"temp_media_{uuid.uuid4()}{Path(media_file.filename).suffix}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            print(f"🎬 Processing uploaded media file: {media_file.filename}")
            
            # Save the uploaded file
            media_file.save(temp_path)
            
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
            raise Exception(error_msg)
    
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
        """Get list of supported audio and video formats"""
        return self.supported_formats.copy()
    
    def get_audio_formats(self) -> list:
        """Get list of supported audio formats only"""
        audio_formats = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.mpga']
        return audio_formats
    
    def get_video_formats(self) -> list:
        """Get list of supported video formats only"""
        video_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpeg', '.mpg']
        return video_formats
    
    def is_media_file(self, filename: str) -> bool:
        """Check if a filename is a supported media file"""
        if not filename:
            return False
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.supported_formats
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]