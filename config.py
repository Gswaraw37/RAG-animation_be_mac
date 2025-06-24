import os
from dotenv import load_dotenv

load_dotenv(override=True)
print(f"DEBUG [config.py]: MYSQL_USER from os.environ: '{os.environ.get('MYSQL_USER')}'")
print(f"DEBUG [config.py]: MYSQL_PORT from os.environ: '{os.environ.get('MYSQL_PORT')}'")
print(f"DEBUG [config.py]: COLLECTION_NAME from os.environ: '{os.environ.get('COLLECTION_NAME')}'")

class Config:
    """Set Flask configuration variables from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK_ENV')

    # Database Config
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', 3306)

    # RAG System Config
    LLM_MODEL_PATH = os.environ.get('LLM_MODEL_PATH')
    MODEL_CACHE_DIR = os.environ.get('MODEL_CACHE_DIR')
    EMBEDDING_MODEL_NAME = os.environ.get('EMBEDDING_MODEL_NAME')
    CHROMA_PERSIST_DIRECTORY = os.environ.get('CHROMA_PERSIST_DIRECTORY')
    UPLOAD_FOLDER = os.environ.get('UPLOADS_FOLDER')
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    COLLECTION_NAME = os.environ.get('COLLECTION_NAME')
    
    # Digital Human & TTS Config
    TTS_PROVIDER = os.environ.get('TTS_PROVIDER', 'elevenlabs')
    ELEVEN_LABS_API_KEY = os.environ.get('ELEVEN_LABS_API_KEY')
    ELEVEN_LABS_VOICE_ID = os.environ.get('ELEVEN_LABS_VOICE_ID', 'v70fYBHUOrHA3AKIBjPq')
    ELEVEN_LABS_MODEL_ID = os.environ.get('ELEVEN_LABS_MODEL_ID', 'eleven_multilingual_v2')
    
    # Lip Sync Config
    RHUBARB_PATH = os.environ.get('RHUBARB_PATH', './bin/rhubarb.exe')
    
    # Audio Config
    AUDIO_OUTPUT_DIR = os.environ.get('AUDIO_OUTPUT_DIR', './audios')
    TEMP_DIR = os.environ.get('TEMP_DIR', './temp')

    # Hugging Face Hub API Token
    HUGGINGFACEHUB_API_TOKEN = os.environ.get('HUGGINGFACEHUB_API_TOKEN')

    # Langchain
    LANGCHAIN_TRACING_V2 = os.environ.get('LANGCHAIN_TRACING_V2')
    LANGCHAIN_API_KEY = os.environ.get('LANGCHAIN_API_KEY')
    LANGCHAIN_PROJECT = os.environ.get('LANGCHAIN_PROJECT')

    # Admin Credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

    if UPLOAD_FOLDER and not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    if LLM_MODEL_PATH:
        llm_model_dir = os.path.dirname(LLM_MODEL_PATH)
        if llm_model_dir and not os.path.exists(llm_model_dir) and llm_model_dir.startswith('./'):
            os.makedirs(llm_model_dir)

    if CHROMA_PERSIST_DIRECTORY and not os.path.exists(CHROMA_PERSIST_DIRECTORY):
        os.makedirs(CHROMA_PERSIST_DIRECTORY)

