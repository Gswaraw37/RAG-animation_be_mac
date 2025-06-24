from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import os
from functools import wraps
import uuid

from config import Config
from database import log_uploaded_file, get_all_uploaded_files, update_file_processed_status
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
@admin_required
def admin_dashboard():
    """Menampilkan dashboard admin, termasuk daftar file yang diunggah."""
    files = get_all_uploaded_files()
    return render_template('admin_upload.html', uploaded_files=files)

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

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


        return redirect(url_for('admin.admin_dashboard'))
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
    return redirect(url_for('admin.admin_dashboard'))
