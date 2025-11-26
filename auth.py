"""Authentication service and routes."""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_user_by_username, get_user_by_id, create_user, user_exists

auth_bp = Blueprint('auth', __name__)
MIN_PASSWORD_LENGTH = 6


def login_required(f):
    """Require authentication for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def register_user(username: str, password: str):
    """Register a new user. Returns (success, message, user)."""
    username = username.strip()
    if not username:
        return False, "Username required", None
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters", None
    if user_exists(username):
        return False, "Username taken", None
    
    user = create_user(username, generate_password_hash(password, method='pbkdf2:sha256'))
    return True, "OK", user


def authenticate(username: str, password: str):
    """Authenticate user. Returns User or None."""
    if not username or not password:
        return None
    user = get_user_by_username(username.strip())
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        user = authenticate(request.form.get('username', ''), request.form.get('password', ''))
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        error = 'Invalid username or password'
    return render_template('login.html', error=error)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        success, msg, user = register_user(request.form.get('username', ''), request.form.get('password', ''))
        if success:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        error = msg
    return render_template('register.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
