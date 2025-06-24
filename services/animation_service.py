import random
from flask import current_app
import logging

# Use regular Python logging for initialization
logger = logging.getLogger(__name__)

class AnimationService:
    def __init__(self):
        self.setup_animation_mappings()
    
    def _get_logger(self):
        """Get the appropriate logger (Flask app logger if available, otherwise Python logger)"""
        try:
            return current_app.logger
        except RuntimeError:
            return logger
    
    def setup_animation_mappings(self):
        """Setup mapping antara emosi dan animasi"""
        self.emotion_animations = {
            'default': ['Idle', 'Ngobrol1', 'Ngobrol2'],
            'smile': ['Ngobrol1', 'Ngobrol2'],
            'sad': ['Sad', 'Ngobrol1'],
        }
        
        # Mapping berdasarkan topik/konteks (khusus untuk domain gizi)
        self.context_animations = {
            'greeting': ['Ngobrol1', 'Ngobrol2'],
            'explanation': ['Ngobrol2', 'Ngobrol1'],
            'positive_advice': ['Ngobrol1', 'Ngobrol2'],
            'concern': ['Sad'],
            'encouragement': ['Ngobrol2', 'Ngobrol1']
        }
        
        # Available animations (sesuai dengan yang akan dibuat di frontend)
        self.available_animations = [
            'Idle',
            'Ngobrol1', 
            'Ngobrol2',
            'Sad',
        ]
    
    def get_animation_for_emotion(self, emotion, context=None):
        """
        Dapatkan animasi berdasarkan emosi dan konteks
        """
        try:
            # Prioritas: context-specific animation > emotion-based animation > default
            animation = None
            
            # Cek context-based animation dulu
            if context and context in self.context_animations:
                animation = random.choice(self.context_animations[context])
            
            # Jika tidak ada context animation, gunakan emotion-based
            elif emotion in self.emotion_animations:
                animation = random.choice(self.emotion_animations[emotion])
            
            # Fallback ke default
            else:
                animation = random.choice(self.emotion_animations['default'])
            
            # Pastikan animasi yang dipilih tersedia
            if animation not in self.available_animations:
                animation = 'Ngobrol1'  # Safe fallback
            
            return animation
            
        except Exception as e:
            self._get_logger().error(f"Error getting animation: {e}")
            return 'Ngobrol1'  # Safe fallback
    
    def analyze_response_context(self, response_text):
        """
        Analisis konteks dari response untuk menentukan animasi yang tepat
        """
        if not response_text:
            return 'explanation'
            
        response_lower = response_text.lower()
        
        # Greeting context
        if any(word in response_lower for word in ['halo', 'hai', 'selamat', 'salam']):
            return 'greeting'
        
        # Positive advice context
        elif any(word in response_lower for word in ['bagus', 'baik', 'sehat', 'disarankan', 'sebaiknya']):
            return 'positive_advice'
        
        # Concern context
        elif any(word in response_lower for word in ['kurang', 'tidak cukup', 'perlu perhatian', 'masalah', 'bahaya', 'risiko', 'hati-hati', 'jangan', 'hindari']):
            return 'concern'
        
        # Encouragement context
        elif any(word in response_lower for word in ['terus', 'lanjutkan', 'pertahankan', 'semangat']):
            return 'encouragement'
        
        # Explanation context (default untuk jawaban informatif)
        else:
            return 'explanation'
    
    def get_facial_expression_for_context(self, context, emotion='default'):
        """
        Dapatkan facial expression berdasarkan konteks dan emosi
        """
        context_expressions = {
            'greeting': 'smile',
            'positive_advice': 'smile',
            'concern': 'sad',
            'encouragement': 'smile',
            'explanation': 'default'
        }
        
        # Prioritas: explicit emotion > context-based expression > default
        if emotion != 'default':
            return emotion
        elif context in context_expressions:
            return context_expressions[context]
        else:
            return 'default'
    
    def get_animation_sequence(self, response_parts):
        """
        Generate sequence animasi untuk multiple parts response
        Memastikan variasi animasi yang natural
        """
        animations = []
        last_animation = None
        
        for i, part in enumerate(response_parts):
            context = self.analyze_response_context(part.get('text', ''))
            emotion = part.get('emotion', 'default')
            
            # Dapatkan animasi kandidat
            candidates = self.emotion_animations.get(emotion, self.emotion_animations['default'])
            
            # Hindari animasi yang sama berturut-turut
            available_candidates = [anim for anim in candidates if anim != last_animation]
            if not available_candidates:
                available_candidates = candidates
            
            animation = random.choice(available_candidates)
            animations.append(animation)
            last_animation = animation
        
        return animations
    
    def enhance_response_with_animation(self, response_parts):
        """
        Enhance response parts dengan animation dan facial expression data
        """
        enhanced_parts = []
        
        for i, part in enumerate(response_parts):
            text = part.get('text', '')
            context = self.analyze_response_context(text)
            
            base_emotion = part.get('emotion', 'default')
            facial_expression = self.get_facial_expression_for_context(context, base_emotion)
            animation = self.get_animation_for_emotion(base_emotion, context)
            
            enhanced_part = {
                'text': text,
                'emotion': base_emotion,
                'facialExpression': facial_expression,
                'animation': animation,
                'context': context
            }
            
            enhanced_parts.append(enhanced_part)
        
        return enhanced_parts

animation_service = AnimationService()

def get_emotion_animation(emotion, context=None):
    """
    Public function untuk mendapatkan animasi berdasarkan emosi
    """
    return animation_service.get_animation_for_emotion(emotion, context)

def enhance_response_with_animation(response_parts):
    """
    Public function untuk enhance response dengan animation data
    """
    return animation_service.enhance_response_with_animation(response_parts)