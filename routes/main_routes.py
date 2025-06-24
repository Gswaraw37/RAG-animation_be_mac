from flask import Blueprint, render_template, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
import os
import uuid

from rag_system import get_rag_response, initialize_rag_components
from database import get_chat_history as db_get_chat_history

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """Menampilkan halaman dashboard utama."""
    return render_template('dashboard.html')

@main_bp.route('/chatbot')
def chatbot_page():
    """Menampilkan halaman chatbot."""
    if 'chat_session_uuid' not in session:
        session['chat_session_uuid'] = str(uuid.uuid4())
        current_app.logger.info(f"Sesi chat baru dimulai: {session['chat_session_uuid']}")
    return render_template('chatbot.html')

@main_bp.route('/chat', methods=['POST'])
def handle_chat():
    """Menerima pesan dari pengguna dan mengembalikan respons dari RAG."""
    data = request.json
    user_message = data.get('message')
    session_uuid_from_client = data.get('session_uuid')

    if not user_message:
        return jsonify({"error": "Pesan tidak boleh kosong."}), 400

    if session_uuid_from_client:
        current_session_uuid = session_uuid_from_client
        if 'chat_session_uuid' not in session or session['chat_session_uuid'] != current_session_uuid:
            session['chat_session_uuid'] = current_session_uuid
            current_app.logger.info(f"Melanjutkan sesi chat dari klien: {current_session_uuid}")
    elif 'chat_session_uuid' in session:
        current_session_uuid = session['chat_session_uuid']
    else:
        current_session_uuid = str(uuid.uuid4())
        session['chat_session_uuid'] = current_session_uuid
        current_app.logger.info(f"Sesi chat baru dibuat oleh server: {current_session_uuid}")
    
    try:
        bot_reply = get_rag_response(current_session_uuid, user_message)
        return jsonify({"reply": bot_reply, "session_uuid": current_session_uuid})
    except Exception as e:
        current_app.logger.error(f"Error di endpoint /chat: {e}", exc_info=True)
        return jsonify({"reply": "Maaf, terjadi kesalahan internal.", "session_uuid": current_session_uuid}), 500

@main_bp.route('/get_history', methods=['GET'])
def get_history():
    """Mengambil riwayat chat untuk session_uuid tertentu."""
    session_uuid_param = request.args.get('session_uuid')

    if not session_uuid_param:
        if 'chat_session_uuid' in session:
            session_uuid_param = session['chat_session_uuid']
        else:
            return jsonify([])

    history = db_get_chat_history(session_uuid_param)
    return jsonify(history)

