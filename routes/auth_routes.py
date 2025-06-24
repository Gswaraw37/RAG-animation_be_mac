from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database import verify_user
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Menangani login admin."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username dan password harus diisi.', 'error')
            return render_template('login.html')

        user = verify_user(username, password)

        if user and user.get('is_admin'):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = True
            flash('Login berhasil!', 'success')
            current_app.logger.info(f"Admin '{username}' berhasil login.")
            return redirect(url_for('admin.admin_dashboard'))
        else:
            if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
                session['user_id'] = 'default_admin'
                session['username'] = Config.ADMIN_USERNAME
                session['is_admin'] = True
                flash('Login berhasil (menggunakan kredensial default)! Harap pastikan admin ada di database.', 'info')
                current_app.logger.info(f"Admin '{username}' berhasil login menggunakan kredensial default.")
                return redirect(url_for('admin.admin_dashboard'))
            
            flash('Username atau password salah.', 'error')
            current_app.logger.warning(f"Percobaan login gagal untuk username: {username}")
            return render_template('login.html')

    if session.get('is_admin'):
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Menangani logout admin."""
    username = session.get('username', 'Admin')
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    session.pop('chat_session_uuid', None)
    flash('Anda telah berhasil logout.', 'success')
    current_app.logger.info(f"Admin '{username}' berhasil logout.")
    return redirect(url_for('main.dashboard'))
