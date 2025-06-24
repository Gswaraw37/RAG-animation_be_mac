from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import json
import uuid
import base64
import os
import subprocess
from io import BytesIO
import tempfile
from datetime import datetime

from rag_system import get_rag_response
from database import insert_chat_log

from services.tts_service import convert_text_to_speech
from services.lip_sync_service import generate_lip_sync
from services.animation_service import get_emotion_animation

digital_human_bp = Blueprint('digital_human', __name__, url_prefix='/api/digital-human')

@digital_human_bp.route('/chat', methods=['POST'])
@cross_origin()
def chat_with_avatar():
    """
    Endpoint untuk chat dengan avatar digital human
    Input: text message atau audio (base64)
    Output: response dengan text, audio, animation, facial expression, dan lip-sync data
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        session_uuid = data.get('session_uuid', str(uuid.uuid4()))
        message_type = data.get('type', 'text')
        
        if message_type == 'audio':
            audio_data = data.get('audio_data', '')
            user_message = convert_audio_to_text(audio_data)
            current_app.logger.info(f"Audio converted to text: {user_message}")
            
            if not user_message or user_message.strip() == "":
                return jsonify({
                    "messages": [{
                        "text": "Maaf, saya tidak dapat memahami audio yang Anda berikan. Silakan coba lagi atau gunakan text.",
                        "facialExpression": "sad",
                        "animation": "Sad",
                        "audio": "",
                        "lipsync": {"metadata": {"duration": 3.0}, "mouthCues": []}
                    }],
                    "session_uuid": session_uuid
                }), 200
        
        if not user_message:
            return jsonify({"error": "Message tidak boleh kosong"}), 400
            
        rag_response = get_rag_response(session_uuid, user_message)
        emotion_data = analyze_response_emotion(rag_response)
        message_parts = split_response_into_parts(rag_response, max_parts=3)
        
        response_messages = []
        for i, part in enumerate(message_parts):
            try:
                audio_file = convert_text_to_speech(part['text'], f"temp_audio_{session_uuid}_{i}")
                
                lip_sync_data = generate_lip_sync(audio_file) if audio_file else create_fallback_lipsync()
                
                audio_base64 = audio_file_to_base64(audio_file) if audio_file else ""
                
                message_obj = {
                    "text": part['text'],
                    "facialExpression": part.get('emotion', 'default'),
                    "animation": part.get('animation', 'Idle'),
                    "audio": audio_base64,
                    "lipsync": lip_sync_data
                }
                response_messages.append(message_obj)
                
                if audio_file and os.path.exists(audio_file):
                    os.remove(audio_file)
                    
            except Exception as e:
                current_app.logger.error(f"Error processing message part {i}: {e}")
                message_obj = {
                    "text": part['text'],
                    "facialExpression": "default",
                    "animation": "Idle",
                    "audio": "",
                    "lipsync": create_fallback_lipsync()
                }
                response_messages.append(message_obj)
        
        return jsonify({
            "messages": response_messages,
            "session_uuid": session_uuid
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in chat_with_avatar: {e}", exc_info=True)
        
        error_message = {
            "text": "Maaf, terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi.",
            "facialExpression": "sad",
            "animation": "Sad",
            "audio": "",
            "lipsync": create_fallback_lipsync()
        }
        
        return jsonify({
            "messages": [error_message],
            "session_uuid": session_uuid or str(uuid.uuid4())
        }), 200

def analyze_response_emotion(response_text):
    """
    Analisis emosi dari response text untuk menentukan facial expression dan animation
    """
    if not response_text:
        return {'emotion': 'default', 'animation': 'Idle'}
        
    response_lower = response_text.lower()
    
    if any(word in response_lower for word in ['senang', 'gembira', 'baik', 'bagus', 'hebat', 'sehat', 'wow', 'hebat', 'luar biasa', 'mengejutkan', 'bahaya', 'hati-hati', 'jangan', 'hindari']):
        return {'emotion': 'smile', 'animation': 'Ngobrol2'}
    elif any(word in response_lower for word in ['sedih', 'buruk', 'tidak', 'maaf', 'kurang']):
        return {'emotion': 'sad', 'animation': 'Sad'}
    else:
        return {'emotion': 'default', 'animation': 'Ngobrol1'}

def split_response_into_parts(response_text, max_parts=3):
    """
    Split response panjang menjadi beberapa bagian dengan emotion yang berbeda
    """
    if not response_text:
        return [{'text': 'Maaf, tidak ada response yang tersedia.', 'emotion': 'sad', 'animation': 'Sad'}]
    
    sentences = [s.strip() for s in response_text.split('.') if s.strip()]
    
    if len(sentences) <= max_parts:
        parts = []
        for sentence in sentences:
            if sentence:
                emotion_data = analyze_response_emotion(sentence)
                parts.append({
                    'text': sentence + ('.' if not sentence.endswith('.') else ''),
                    'emotion': emotion_data['emotion'],
                    'animation': emotion_data['animation']
                })
        return parts if parts else [{'text': response_text, 'emotion': 'default', 'animation': 'Ngobrol1'}]
    
    part_size = max(1, len(sentences) // max_parts)
    parts = []
    
    for i in range(max_parts):
        start_idx = i * part_size
        end_idx = (i + 1) * part_size if i < max_parts - 1 else len(sentences)
        
        if start_idx >= len(sentences):
            break
            
        part_sentences = sentences[start_idx:end_idx]
        part_text = '. '.join(part_sentences)
        if part_text and not part_text.endswith('.'):
            part_text += '.'
            
        emotion_data = analyze_response_emotion(part_text)
        parts.append({
            'text': part_text,
            'emotion': emotion_data['emotion'],
            'animation': emotion_data['animation']
        })
    
    return parts if parts else [{'text': response_text, 'emotion': 'default', 'animation': 'Ngobrol1'}]

def audio_file_to_base64(file_path):
    """
    Convert audio file ke base64 string
    """
    try:
        if not file_path or not os.path.exists(file_path):
            return ""
            
        with open(file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            return base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Error converting audio to base64: {e}")
        return ""

def create_fallback_lipsync():
    """
    Create fallback lip-sync data
    """
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

@digital_human_bp.route('/test', methods=['GET'])
@cross_origin()
def test_endpoint():
    """Test endpoint untuk memastikan service berjalan"""
    return jsonify({
        "status": "OK",
        "message": "Digital Human service is running", 
        "timestamp": datetime.now().isoformat()
    })