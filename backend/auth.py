from flask import session, redirect, url_for, request, jsonify
from functools import wraps

# Simple user store (in production, use a database)
USERS = {
    "admin": "password123"
}

# Decorator to require login for routes

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Login handler

def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username in USERS and USERS[username] == password:
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Logout handler

def logout():
    session.clear()
    return jsonify({"message": "Logged out"})