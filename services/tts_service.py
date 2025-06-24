import os
import tempfile
import subprocess
from pathlib import Path
import requests
import json
import logging

# Setup logger untuk digunakan di luar Flask context
logger = logging.getLogger(__name__)

def get_logger():
    """Get appropriate logger - Flask app logger jika dalam context, atau standard logger"""
    try:
        from flask import current_app
        return current_app.logger
    except RuntimeError:
        # Di luar Flask context, gunakan standard logger
        return logger

class TTSService:
    def __init__(self):
        self.provider = os.getenv('TTS_PROVIDER', 'local')
        self.api_key = None
        self.voice_id = None
        self.setup_provider()
    
    def setup_provider(self):
        """Setup TTS provider berdasarkan konfigurasi"""
        if self.provider == 'elevenlabs':
            self.api_key = os.getenv('ELEVEN_LABS_API_KEY')
            self.voice_id = os.getenv('ELEVEN_LABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')
            if not self.api_key:
                get_logger().warning("ElevenLabs API key not found, falling back to local TTS")
                self.provider = 'local'
    
    def convert_text_to_speech(self, text, filename_prefix="audio"):
        """Convert text ke audio file"""
        try:
            get_logger().info(f"Converting text to speech: '{text[:50]}...' using provider: {self.provider}")
            
            if self.provider == 'elevenlabs' and self.api_key:
                return self._elevenlabs_tts(text, filename_prefix)
            else:
                return self._local_tts(text, filename_prefix)
        except Exception as e:
            get_logger().error(f"TTS conversion failed: {e}")
            return self._local_tts(text, filename_prefix)
    
    def _elevenlabs_tts(self, text, filename_prefix):
        """ElevenLabs TTS implementation"""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            audio_dir = Path("audios")
            audio_dir.mkdir(exist_ok=True)
            
            audio_path = audio_dir / f"{filename_prefix}.mp3"
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            get_logger().info(f"ElevenLabs TTS success: {audio_path}")
            return str(audio_path)
        else:
            raise Exception(f"ElevenLabs API error: {response.status_code}, {response.text}")
    
    def _local_tts(self, text, filename_prefix):
        """Local TTS dengan multiple fallback options"""
        audio_dir = Path("audios")
        audio_dir.mkdir(exist_ok=True)
        audio_path = audio_dir / f"{filename_prefix}.wav"
        
        # Option 1: Coba espeak dengan English voice
        if self._try_espeak(text, audio_path):
            return str(audio_path)
        
        # Option 2: Coba Windows SAPI (Speech API)
        if self._try_windows_sapi(text, audio_path):
            return str(audio_path)
        
        # Option 3: Fallback ke synthetic audio dengan beeps
        return self._create_synthetic_audio(text, filename_prefix)
    
    def _try_espeak(self, text, audio_path):
        """Try espeak with different voice options"""
        voice_options = ['en', 'en-us', 'en+f3', None]
        
        for voice in voice_options:
            try:
                cmd = ["espeak", "-s", "150", "-w", str(audio_path)]
                if voice:
                    cmd.extend(["-v", voice])
                cmd.append(text)
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    get_logger().info(f"espeak success with voice: {voice}")
                    return True
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                get_logger().debug(f"espeak failed with voice {voice}: {e}")
                continue
        
        return False
    
    def _try_windows_sapi(self, text, audio_path):
        """Try Windows Speech API using PowerShell"""
        try:
            # Escape quotes dalam text
            safe_text = text.replace('"', '""')
            
            # PowerShell script untuk Windows SAPI
            ps_script = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile("{audio_path}")
$synth.Speak("{safe_text}")
$synth.Dispose()
'''
            
            cmd = ["powershell", "-Command", ps_script]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                get_logger().info("Windows SAPI TTS success")
                return True
                
        except Exception as e:
            get_logger().debug(f"Windows SAPI failed: {e}")
        
        return False
    
    def _create_synthetic_audio(self, text, filename_prefix):
        """Create synthetic audio dengan beeps dan tones"""
        try:
            audio_dir = Path("audios")
            audio_path = audio_dir / f"{filename_prefix}.wav"
            
            # Calculate duration based on text length
            duration = max(2.0, len(text) * 0.08)
            
            # Create audio dengan beeps menggunakan ffmpeg
            cmd = [
                "ffmpeg", "-f", "lavfi", 
                "-i", f"sine=frequency=440:duration={duration}",
                "-ar", "22050", "-ac", "1", "-y", str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(audio_path):
                get_logger().info(f"Synthetic audio created: {audio_path}")
                return str(audio_path)
            else:
                return self._create_minimal_audio(filename_prefix)
                
        except Exception as e:
            get_logger().error(f"Synthetic audio creation failed: {e}")
            return self._create_minimal_audio(filename_prefix)
    
    def _create_minimal_audio(self, filename_prefix):
        """Create minimal WAV file as last resort"""
        try:
            audio_dir = Path("audios")
            audio_path = audio_dir / f"{filename_prefix}.wav"
            
            # Create basic WAV header + silent audio
            import struct
            import wave
            
            with wave.open(str(audio_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(22050)  # 22kHz
                
                # Create 3 seconds of silence
                frames = 22050 * 3
                data = struct.pack('<' + 'h' * frames, *([0] * frames))
                wav_file.writeframes(data)
            
            get_logger().info(f"Minimal audio file created: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            get_logger().error(f"Failed to create minimal audio: {e}")
            return None

# Global instance - sekarang aman untuk diinisialisasi
tts_service = TTSService()

def convert_text_to_speech(text, filename_prefix="audio"):
    """Public function untuk convert text ke speech"""
    return tts_service.convert_text_to_speech(text, filename_prefix)