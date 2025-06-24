from flask import Flask, redirect, url_for
from flask_cors import CORS
from config import Config
from database import create_tables, add_admin_user_if_not_exists
from rag_system import initialize_rag_components
import logging
import os

# Impor Blueprint
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.digital_human_routes import digital_human_bp

def create_app():
    """Membuat dan mengkonfigurasi instance aplikasi Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])
    
    print(f"DEBUG [app.py]: Config.MYSQL_USER loaded: '{app.config.get('MYSQL_USER')}'")
    print(f"DEBUG [app.py]: Config.MYSQL_PORT loaded: '{app.config.get('MYSQL_PORT')}'")
    print(f"DEBUG [app.py]: Config.COLLECTION_NAME loaded: '{app.config.get('COLLECTION_NAME')}'")

    logging.basicConfig(level=logging.INFO)

    app.logger.info("Memulai aplikasi GiziAI...")
    app.logger.info(f"Environment: {Config.FLASK_ENV}")
    app.logger.info(f"Upload folder: {Config.UPLOAD_FOLDER}")
    app.logger.info(f"Chroma DB persist directory: {Config.CHROMA_PERSIST_DIRECTORY}")
    app.logger.info(f"LLM Model Path: {Config.LLM_MODEL_PATH}")

    with app.app_context():
        app.logger.info("Menginisialisasi database...")
        create_tables()
        if Config.ADMIN_USERNAME and Config.ADMIN_PASSWORD:
            add_admin_user_if_not_exists(Config.ADMIN_USERNAME, Config.ADMIN_PASSWORD)
        else:
            app.logger.warning("ADMIN_USERNAME atau ADMIN_PASSWORD tidak diatur di .env. Admin default tidak dibuat.")
        app.logger.info("Inisialisasi database selesai.")

        app.logger.info("Menginisialisasi komponen RAG (LLM, Embeddings, Vectorstore)...")
        initialize_rag_components()
        app.logger.info("Inisialisasi komponen RAG selesai.")
        
        os.makedirs("audios", exist_ok=True)
        os.makedirs("temp", exist_ok=True)
        app.logger.info("Direktori untuk digital human telah dibuat.")

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)
    app.register_blueprint(digital_human_bp)

    @app.route('/')
    def index():
        return redirect(url_for('admin.dashboard'))
    
    app.logger.info("Aplikasi GiziAI berhasil dikonfigurasi dan siap dijalankan.")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=(Config.FLASK_ENV == 'development'))
