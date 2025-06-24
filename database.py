import mysql.connector
from mysql.connector import Error
import bcrypt
from config import Config
from datetime import datetime

def get_db_connection():
    """Membuat dan mengembalikan koneksi ke database MySQL."""
    try:
        try:
            port_number = int(Config.MYSQL_PORT)
        except ValueError:
            print(f"Error: MYSQL_PORT '{Config.MYSQL_PORT}' bukan angka yang valid. Menggunakan port default 3306 jika memungkinkan.")
            port_number = 3306
        
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=port_number
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error saat menghubungkan ke MySQL: {e}")
        return None

def create_tables():
    """Membuat tabel yang diperlukan jika belum ada."""
    conn = get_db_connection()
    if conn is None:
        print("Tidak dapat membuat tabel, koneksi database gagal.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Tabel 'users' berhasil diperiksa/dibuat.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                filepath VARCHAR(512) NOT NULL,
                file_type VARCHAR(50),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL,
                uploader_id INT,
                FOREIGN KEY (uploader_id) REFERENCES users(id)
            )
        """)
        print("Tabel 'uploaded_files' berhasil diperiksa/dibuat.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_uuid VARCHAR(255) NOT NULL,
                user_query TEXT,
                bot_response TEXT,
                model_used VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Tabel 'chat_logs' berhasil diperiksa/dibuat.")

        conn.commit()
    except Error as e:
        print(f"Error saat membuat tabel: {e}")
    finally:
        cursor.close()
        conn.close()

def add_admin_user_if_not_exists(username, password):
    """Menambahkan pengguna admin jika belum ada."""
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"Admin user '{username}' sudah ada.")
            return True

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
            (username, hashed_password.decode('utf-8'), True)
        )
        conn.commit()
        print(f"Admin user '{username}' berhasil ditambahkan.")
        return True
    except Error as e:
        print(f"Error saat menambahkan admin user: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_user(username, password):
    """Memverifikasi kredensial pengguna."""
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return user
        return None
    except Error as e:
        print(f"Error saat memverifikasi user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def log_uploaded_file(filename, filepath, file_type, uploader_id):
    """Mencatat metadata file yang diunggah ke database."""
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO uploaded_files (filename, filepath, file_type, uploader_id) VALUES (%s, %s, %s, %s)",
            (filename, filepath, file_type, uploader_id)
        )
        conn.commit()
        print(f"File '{filename}' berhasil dicatat di database.")
        return True
    except Error as e:
        print(f"Error saat mencatat file: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_uploaded_files():
    """Mengambil semua daftar file yang telah diunggah."""
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, filename, filepath, file_type, uploaded_at, processed_at FROM uploaded_files ORDER BY uploaded_at DESC")
        files = cursor.fetchall()
        return files
    except Error as e:
        print(f"Error saat mengambil daftar file: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_file_processed_status(file_id):
    """Memperbarui status file menjadi sudah diproses (misalnya, setelah di-embed)."""
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE uploaded_files SET processed_at = %s WHERE id = %s",
            (datetime.now(), file_id)
        )
        conn.commit()
        print(f"Status proses untuk file ID {file_id} berhasil diperbarui.")
        return True
    except Error as e:
        print(f"Error saat memperbarui status proses file: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
        
def get_unprocessed_files():
    """Mengambil semua file yang belum diproses (processed_at IS NULL)."""
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, filename, filepath, file_type FROM uploaded_files WHERE processed_at IS NULL ORDER BY uploaded_at ASC")
        files = cursor.fetchall()
        return files
    except Error as e:
        print(f"Error saat mengambil file yang belum diproses: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def insert_chat_log(session_uuid, user_query, bot_response, model_used):
    """Menyimpan log interaksi chat ke database."""
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_logs (session_uuid, user_query, bot_response, model_used) VALUES (%s, %s, %s, %s)",
            (session_uuid, user_query, bot_response, model_used)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error saat menyimpan chat log: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_chat_history(session_uuid):
    """Mengambil riwayat chat berdasarkan session_uuid."""
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_query, bot_response FROM chat_logs WHERE session_uuid = %s ORDER BY created_at ASC",
            (session_uuid,)
        )
        history = []
        for row in cursor.fetchall():
            if row['user_query']:
                history.append({"role": "human", "content": row['user_query']})
            if row['bot_response']:
                history.append({"role": "ai", "content": row['bot_response']})
        return history
    except Error as e:
        print(f"Error saat mengambil riwayat chat: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("Menginisialisasi database...")
    create_tables()
    print("Pengecekan admin default...")
    if Config.ADMIN_USERNAME and Config.ADMIN_PASSWORD:
        add_admin_user_if_not_exists(Config.ADMIN_USERNAME, Config.ADMIN_PASSWORD)
    else:
        print("ADMIN_USERNAME atau ADMIN_PASSWORD tidak diatur di .env. Admin default tidak dibuat.")
    print("Inisialisasi database selesai.")