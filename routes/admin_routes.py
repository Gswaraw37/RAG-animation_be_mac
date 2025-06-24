from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from functools import wraps
import uuid

from config import Config
from database import log_uploaded_file, get_all_uploaded_files, update_file_processed_status, get_all_uploaded_files, insert_file_and_return_id, delete_file_from_db, get_chat_sessions_summary, delete_chat_history_by_session, get_file_by_id, get_total_message_count
from rag_system import process_document_to_vectorstore, process_pending_documents

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Anda harus login sebagai admin untuk mengakses halaman ini.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard admin utama"""
    try:
        files = get_all_uploaded_files()
        sessions = get_chat_sessions_summary()
        total_messages = get_total_message_count()
        
        stats = {
            'total_files': len(files),
            'total_sessions': len(sessions),
            'total_messages': total_messages,
            'recent_files': files[:5] if files else [],
            'recent_sessions': sessions[:5] if sessions else []
        }
        
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        current_app.logger.error(f"Error loading dashboard: {e}")
        flash('Gagal memuat dashboard', 'error')
        return render_template('admin/dashboard.html', stats={})

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
           
@admin_bp.route('/files')
@admin_required
def files():
    """Halaman manajemen file"""
    try:
        files = get_all_uploaded_files()
        return render_template('admin/files.html', files=files)
    except Exception as e:
        current_app.logger.error(f"Error loading files page: {e}")
        flash('Gagal memuat halaman file', 'error')
        return render_template('admin/files.html', files=[])
    
@admin_bp.route('/chat-history')
@admin_required
def chat_history():
    """Halaman riwayat chat"""
    try:
        sessions = get_chat_sessions_summary()
        return render_template('admin/chat_history.html', sessions=sessions)
    except Exception as e:
        current_app.logger.error(f"Error loading chat history page: {e}")
        flash('Gagal memuat halaman chat history', 'error')
        return render_template('admin/chat_history.html', sessions=[])
    
@admin_bp.route('/api/files', methods=['GET'])
@admin_required
def api_get_files():
    """API: Mendapatkan semua file yang sudah diupload"""
    try:
        files = get_all_uploaded_files()
        return jsonify({
            "success": True,
            "data": files,
            "total": len(files)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting files: {e}")
        return jsonify({
            "success": False,
            "message": "Gagal mengambil data file"
        }), 500

@admin_bp.route('/api/files/upload', methods=['POST'])
@admin_required
def api_upload_file():
    """API: Upload file PDF atau DOCX"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "Tidak ada file yang dipilih"
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "Tidak ada file yang dipilih"
            }), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            file_id = str(uuid.uuid4())
            file_extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{file_id}.{file_extension}"
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER', './static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, unique_filename)
            file.save(filepath)
            
            file_record_id = insert_file_and_return_id(filename, filepath, file_extension)
            
            if not file_record_id:
                return jsonify({
                    "success": False,
                    "message": "Gagal menyimpan informasi file ke database"
                }), 500
            
            try:
                process_document_to_vectorstore(filepath, file_record_id)
                processing_status = "completed"
            except Exception as e:
                current_app.logger.error(f"Error processing document: {e}")
                processing_status = "failed"
            
            return jsonify({
                "success": True,
                "message": "File berhasil diupload dan diproses",
                "data": {
                    "id": file_record_id,
                    "filename": filename,
                    "filepath": filepath,
                    "processing_status": processing_status
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "Jenis file tidak didukung. Gunakan PDF atau DOCX"
            }), 400

    except Exception as e:
        current_app.logger.error(f"Error uploading file: {e}")
        return jsonify({
            "success": False,
            "message": "Gagal mengupload file"
        }), 500

@admin_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@admin_required
def api_delete_file(file_id):
    """API: Menghapus file berdasarkan ID"""
    try:
        file_info = get_file_by_id(file_id)
        if not file_info:
            return jsonify({
                "success": False,
                "message": "File tidak ditemukan"
            }), 404
        
        if os.path.exists(file_info['filepath']):
            os.remove(file_info['filepath'])
        
        delete_file_from_db(file_id)
        
        return jsonify({
            "success": True,
            "message": "File berhasil dihapus"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {e}")
        return jsonify({
            "success": False,
            "message": "Gagal menghapus file"
        }), 500

@admin_bp.route('/api/chat-sessions', methods=['GET'])
@admin_required
def api_get_chat_sessions():
    """API: Mendapatkan ringkasan session chat"""
    try:
        sessions = get_chat_sessions_summary()
        
        unique_sessions = {}
        for session in sessions:
            session_uuid = session['session_uuid']
            if session_uuid not in unique_sessions:
                unique_sessions[session_uuid] = {
                    'session_uuid': session_uuid,
                    'first_message_time': session['created_at'],
                    'last_message_time': session['created_at'],
                    'message_count': session['message_count'],
                    'first_user_message': session.get('first_user_message', ''),
                    'last_user_message': session.get('last_user_message', '')
                }
            else:
                if session['created_at'] > unique_sessions[session_uuid]['last_message_time']:
                    unique_sessions[session_uuid]['last_message_time'] = session['created_at']
                    unique_sessions[session_uuid]['last_user_message'] = session.get('last_user_message', '')
                unique_sessions[session_uuid]['message_count'] += session['message_count']
        
        sessions_list = list(unique_sessions.values())
        sessions_list.sort(key=lambda x: x['first_message_time'], reverse=True)
        
        return jsonify({
            "success": True,
            "data": sessions_list,
            "total": len(sessions_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting chat sessions: {e}")
        return jsonify({
            "success": False,
            "message": "Gagal mengambil data session chat"
        }), 500

@admin_bp.route('/api/chat-sessions/<session_uuid>', methods=['DELETE'])
@admin_required
def api_delete_chat_session(session_uuid):
    """API: Menghapus semua history chat untuk session_uuid tertentu"""
    try:
        deleted_count = delete_chat_history_by_session(session_uuid)
        
        if deleted_count > 0:
            return jsonify({
                "success": True,
                "message": f"Berhasil menghapus {deleted_count} pesan dari session {session_uuid}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Session tidak ditemukan atau sudah kosong"
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error deleting chat session: {e}")
        return jsonify({
            "success": False,
            "message": "Gagal menghapus session chat"
        }), 500

@admin_bp.route('/api/stats', methods=['GET'])
@admin_required
def api_get_stats():
    """API: Mendapatkan statistik admin dashboard"""
    try:
        files = get_all_uploaded_files()
        sessions = get_chat_sessions_summary()
        total_messages = get_total_message_count()
        
        return jsonify({
            "success": True,
            "data": {
                "total_files": len(files),
                "total_sessions": len(sessions),
                "total_messages": total_messages
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting admin stats: {e}")
        return jsonify({
            "success": False,
            "message": "Gagal mengambil statistik"
        }), 500

@admin_bp.route('/upload', methods=['POST'])
@admin_required
def upload_file():
    """Menangani upload file oleh admin."""
    if 'file' not in request.files:
        flash('Tidak ada bagian file dalam request.', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename 
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        # filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        try:
            if not os.path.exists(Config.UPLOAD_FOLDER):
                os.makedirs(Config.UPLOAD_FOLDER)
                current_app.logger.info(f"Folder upload dibuat di: {Config.UPLOAD_FOLDER}")

            file.save(filepath)
            current_app.logger.info(f"File '{filename}' berhasil disimpan di '{filepath}'")

            uploader_id = session.get('user_id')
            file_type = filename.rsplit('.', 1)[1].lower()
            
            if log_uploaded_file(filename, filepath, file_type, uploader_id):
                flash(f"File '{filename}' berhasil diunggah dan dicatat.", 'success')
                
                process_pending_documents()
                flash(f"Pemrosesan file '{filename}' ke knowledge base telah dimulai/dijadwalkan.", 'info')

            else:
                flash(f"File '{filename}' berhasil diunggah tetapi gagal dicatat di database.", 'warning')

        except Exception as e:
            current_app.logger.error(f"Error saat mengunggah file '{filename}': {e}", exc_info=True)
            flash(f"Terjadi kesalahan saat mengunggah file: {str(e)}", 'error')
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    current_app.logger.info(f"File '{filepath}' dihapus karena gagal unggah/proses.")
                except OSError as oe:
                     current_app.logger.error(f"Gagal menghapus file '{filepath}': {oe}")


        return redirect(url_for('admin.dashboard'))
    else:
        flash('Tipe file tidak diizinkan. Hanya PDF dan DOCX.', 'error')
        return redirect(request.url)

@admin_bp.route('/trigger_processing')
@admin_required
def trigger_processing():
    """Endpoint untuk memicu pemrosesan dokumen yang tertunda secara manual."""
    try:
        current_app.logger.info("Memulai pemrosesan dokumen tertunda secara manual...")
        process_pending_documents()
        flash("Pemrosesan dokumen yang tertunda telah dimulai.", 'info')
    except Exception as e:
        current_app.logger.error(f"Error saat memicu pemrosesan manual: {e}", exc_info=True)
        flash(f"Gagal memulai pemrosesan manual: {str(e)}", 'error')
    return redirect(url_for('admin.dashboard'))
