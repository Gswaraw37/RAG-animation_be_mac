import os
import json
import subprocess
import tempfile
from pathlib import Path
import logging

# Setup logger untuk digunakan di luar Flask context
logger = logging.getLogger(__name__)

def get_logger():
    """Get appropriate logger - Flask app logger jika dalam context, atau standard logger"""
    try:
        from flask import current_app
        return current_app.logger
    except RuntimeError:
        return logger

class LipSyncService:
    def __init__(self):
        self.rhubarb_path = self._find_rhubarb_executable()
        self.setup_directories()
    
    def setup_directories(self):
        """Setup direktori yang diperlukan"""
        self.audios_dir = Path("audios")
        self.audios_dir.mkdir(exist_ok=True)
        
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
    
    def _find_rhubarb_executable(self):
        """Cari executable Rhubarb Lip-Sync"""
        possible_paths = [
            "./bin/rhubarb",
            "./rhubarb/rhubarb",
            "rhubarb",
            "./bin/rhubarb.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        
        get_logger().warning("Rhubarb executable not found. Lip-sync will use fallback method.")
        return None
    
    def _command_exists(self, command):
        """Check apakah command ada di sistem"""
        try:
            subprocess.run([command, "--help"], capture_output=True)
            return True
        except (FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def generate_lip_sync(self, audio_file_path):
        """Generate lip-sync data dari audio file"""
        try:
            if not os.path.exists(audio_file_path):
                return self._create_fallback_lipsync()
            
            if self.rhubarb_path:
                return self._generate_with_rhubarb(audio_file_path)
            else:
                return self._generate_fallback_lipsync(audio_file_path)
                
        except Exception as e:
            get_logger().error(f"Lip-sync generation failed: {e}")
            return self._create_fallback_lipsync()
    
    def _generate_with_rhubarb(self, audio_file_path):
        """Generate lip-sync menggunakan Rhubarb"""
        try:
            # Convert audio ke WAV jika diperlukan
            wav_file = self._ensure_wav_format(audio_file_path)
            
            # Generate lip-sync JSON
            json_output = wav_file.replace('.wav', '.json')
            
            # Run Rhubarb command
            cmd = [
                self.rhubarb_path,
                "-f", "json",
                "-o", json_output,
                wav_file,
                "-r", "phonetic"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(json_output):
                with open(json_output, 'r') as f:
                    lip_sync_data = json.load(f)
                
                # Cleanup temporary files
                self._cleanup_temp_files([wav_file, json_output])
                
                return lip_sync_data
            else:
                get_logger().error(f"Rhubarb failed: {result.stderr}")
                return self._create_fallback_lipsync()
                
        except Exception as e:
            get_logger().error(f"Rhubarb lip-sync failed: {e}")
            return self._create_fallback_lipsync()
    
    def _ensure_wav_format(self, audio_file_path):
        """Convert audio ke WAV format jika belum"""
        audio_path = Path(audio_file_path)
        
        if audio_path.suffix.lower() == '.wav':
            return str(audio_path)
        
        # Convert ke WAV menggunakan ffmpeg
        wav_path = self.temp_dir / f"{audio_path.stem}.wav"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            str(wav_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return str(wav_path)
        except subprocess.CalledProcessError as e:
            get_logger().error(f"FFmpeg conversion failed: {e}")
            return str(audio_path)
    
    def _generate_fallback_lipsync(self, audio_file_path):
        """Generate basic lip-sync data tanpa Rhubarb"""
        try:
            duration = self._estimate_audio_duration(audio_file_path)
            mouth_cues = self._create_basic_mouth_movements(duration)
            
            return {
                "metadata": {
                    "soundFile": os.path.basename(audio_file_path),
                    "duration": duration
                },
                "mouthCues": mouth_cues
            }
            
        except Exception as e:
            get_logger().error(f"Fallback lip-sync failed: {e}")
            return self._create_fallback_lipsync()
    
    def _estimate_audio_duration(self, audio_file_path):
        """Estimate durasi audio"""
        try:
            # Gunakan ffprobe untuk mendapatkan durasi yang akurat
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                audio_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                # Fallback: estimate dari file size
                file_size = os.path.getsize(audio_file_path)
                return max(1.0, file_size / 16000)
                
        except Exception:
            return 3.0
    
    def _create_basic_mouth_movements(self, duration):
        """Create basic mouth movements untuk fallback"""
        mouth_cues = []
        
        # Simple pattern: A -> B -> A cycling
        cue_duration = 0.2
        current_time = 0.0
        
        visemes = ['A', 'B', 'C', 'A', 'B']
        
        while current_time < duration:
            for viseme in visemes:
                if current_time >= duration:
                    break
                
                end_time = min(current_time + cue_duration, duration)
                
                mouth_cues.append({
                    "start": round(current_time, 2),
                    "end": round(end_time, 2),
                    "value": viseme
                })
                
                current_time = end_time
        
        return mouth_cues
    
    def _create_fallback_lipsync(self):
        """Create minimal fallback lip-sync data"""
        return {
            "metadata": {
                "soundFile": "fallback.wav",
                "duration": 3.0
            },
            "mouthCues": [
                {"start": 0.0, "end": 0.5, "value": "A"},
                {"start": 0.5, "end": 1.0, "value": "B"},
                {"start": 1.0, "end": 1.5, "value": "C"},
                {"start": 1.5, "end": 2.0, "value": "A"},
                {"start": 2.0, "end": 2.5, "value": "B"},
                {"start": 2.5, "end": 3.0, "value": "X"}
            ]
        }
    
    def _cleanup_temp_files(self, file_paths):
        """Cleanup temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                get_logger().warning(f"Failed to cleanup {file_path}: {e}")

# Global instance
lip_sync_service = LipSyncService()

def generate_lip_sync(audio_file_path):
    """Public function untuk generate lip-sync"""
    return lip_sync_service.generate_lip_sync(audio_file_path)