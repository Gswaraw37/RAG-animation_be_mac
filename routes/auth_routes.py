from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database import verify_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page untuk admin"""
    if request.method == 'GET':
        if session.get('is_admin'):
            return redirect(url_for('admin.dashboard'))
        return render_template('auth/login.html')
    
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return render_template('auth/login.html')
        
        user = verify_user(username, password)
        
        if user and user.get('is_admin'):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            flash(f'Selamat datang, {user["username"]}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Username atau password salah', 'error')
            return render_template('auth/login.html')

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
    return redirect(url_for('auth.login'))
