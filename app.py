#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRP Web Control Panel - Lightweight Version
Optimized for 2-core 0.5GB RAM lightweight cloud servers
"""

import os
import subprocess
import time
from functools import lru_cache
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Lightweight Flask app configuration
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'frp-web-lightweight')
app.config.update(
    # Optimize for low memory usage
    MAX_CONTENT_LENGTH=1024 * 1024,  # 1MB max request size
    SEND_FILE_MAX_AGE_DEFAULT=3600,  # Cache static files for 1 hour
    PERMANENT_SESSION_LIFETIME=1800,  # 30 min session timeout
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
)

# Configuration - optimized for lightweight deployment
FRPS_SERVICE_NAME = os.environ.get('FRPS_SERVICE', 'frps')
USE_SYSTEMD = os.environ.get('USE_SYSTEMD', 'true').lower() == 'true'
LOGIN_REQUIRED = os.environ.get('LOGIN_REQUIRED', 'true').lower() == 'true'
DEFAULT_USERNAME = os.environ.get('DEFAULT_USER', 'admin')
DEFAULT_PASSWORD = os.environ.get('DEFAULT_PASS', 'admin123')

# Cache for reducing system calls
_status_cache = {'data': None, 'timestamp': 0, 'ttl': 5}  # 5 second cache
_logs_cache = {'data': None, 'timestamp': 0, 'ttl': 10}   # 10 second cache

@lru_cache(maxsize=32)
def get_cached_command_result(command_str, use_sudo=True):
    """Cached command execution to reduce system calls"""
    return execute_command_internal(command_str, use_sudo)

def execute_command_internal(command_str, use_sudo=True):
    """Internal command execution without caching"""
    try:
        cmd = (['sudo'] + command_str.split()) if use_sudo else command_str.split()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': 'Timeout', 'returncode': -1}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -1}

def execute_command(command_str, use_sudo=True, use_cache=False):
    """Execute command with optional caching"""
    if use_cache:
        return get_cached_command_result(command_str, use_sudo)
    return execute_command_internal(command_str, use_sudo)

def get_cached_data(cache_dict, fetch_func, *args):
    """Generic cache helper"""
    now = time.time()
    if cache_dict['data'] is None or (now - cache_dict['timestamp']) > cache_dict['ttl']:
        cache_dict['data'] = fetch_func(*args)
        cache_dict['timestamp'] = now
    return cache_dict['data']

def fetch_frps_status():
    """Fetch frps status (cacheable)"""
    if USE_SYSTEMD:
        result = execute_command(f'systemctl is-active {FRPS_SERVICE_NAME}', use_cache=True)
        is_active = result['stdout'] == 'active'
        return {
            'active': is_active,
            'status': result['stdout'],
            'details': f"Service: {FRPS_SERVICE_NAME} | Status: {result['stdout']}"
        }
    else:
        result = execute_command(f'pgrep -f frps', use_sudo=False, use_cache=True)
        is_active = result['success'] and result['stdout']
        return {
            'active': is_active,
            'status': 'active' if is_active else 'inactive',
            'details': f"PID: {result['stdout']}" if is_active else "Not running"
        }

def fetch_frps_logs(lines=50):
    """Fetch frps logs (cacheable)"""
    if USE_SYSTEMD:
        result = execute_command(f'journalctl -u {FRPS_SERVICE_NAME} -n {lines} --no-pager')
        return result['stdout'] if result['success'] else f"Error: {result['stderr']}"
    else:
        return "Binary mode: logs not available via journalctl"

def get_frps_status():
    """Get cached frps status"""
    return get_cached_data(_status_cache, fetch_frps_status)

def get_frps_logs(lines=50):
    """Get cached frps logs"""
    return get_cached_data(_logs_cache, fetch_frps_logs, lines)

# Authentication helper
def require_auth():
    """Check if authentication is required and valid"""
    if not LOGIN_REQUIRED:
        return True
    return session.get('logged_in', False)

@app.route('/')
def index():
    """Main page - lightweight version"""
    if not require_auth():
        return redirect(url_for('login'))
    
    status = get_frps_status()
    return render_template('index.html',
                         status=status,
                         use_systemd=USE_SYSTEMD,
                         service_name=FRPS_SERVICE_NAME)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Lightweight login"""
    if not LOGIN_REQUIRED:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/status')
def api_status():
    """API: Get service status"""
    if not require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(get_frps_status())

@app.route('/api/logs')
def api_logs():
    """API: Get service logs"""
    if not require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    lines = min(int(request.args.get('lines', 50)), 200)  # Limit max lines
    logs = get_frps_logs(lines)
    return jsonify({'success': True, 'stdout': logs})

@app.route('/api/<action>', methods=['POST'])
def api_action(action):
    """API: Service actions (start/stop/restart)"""
    if not require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if action not in ['start', 'stop', 'restart']:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Clear cache after actions
    _status_cache['data'] = None
    _logs_cache['data'] = None
    get_cached_command_result.cache_clear()
    
    if USE_SYSTEMD:
        result = execute_command(f'systemctl {action} {FRPS_SERVICE_NAME}')
    else:
        if action == 'start':
            result = execute_command('nohup ./frps -c ./frps.yaml > /dev/null 2>&1 &', use_sudo=False)
        elif action == 'stop':
            result = execute_command('pkill -f frps', use_sudo=False)
        else:  # restart
            execute_command('pkill -f frps', use_sudo=False)
            time.sleep(1)
            result = execute_command('nohup ./frps -c ./frps.yaml > /dev/null 2>&1 &', use_sudo=False)
    
    return jsonify(result)

@app.errorhandler(404)
def not_found(error):
    """Lightweight 404 handler"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Lightweight 500 handler"""
    return jsonify({'error': 'Internal server error'}), 500

# Memory optimization: disable debug toolbar and other dev tools in production
if __name__ == '__main__':
    # Lightweight server configuration
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 FRP Web Control Panel (Lightweight) starting on {host}:{port}")
    print(f"💾 Memory optimized for 0.5GB RAM")
    print(f"🔐 Login required: {LOGIN_REQUIRED}")
    if LOGIN_REQUIRED:
        print(f"👤 Default: {DEFAULT_USERNAME}/{DEFAULT_PASSWORD}")
    
    # Use lightweight server settings
    app.run(
        host=host, 
        port=port, 
        debug=debug,
        threaded=True,  # Better for lightweight servers
        use_reloader=False if not debug else True,
        use_debugger=debug
    )
