# app.py
from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
from functools import wraps

app = Flask(__name__, template_folder='.', static_folder='.')
app.secret_key = os.urandom(24)

# Admin credentials (có thể đưa vào biến môi trường sau)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('trangchu.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({'success': True, 'message': 'Đăng nhập thành công'})
    return jsonify({'success': False, 'message': 'Sai tài khoản hoặc mật khẩu'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    return jsonify({'success': True, 'message': 'Đã đăng xuất'})

@app.route('/api/cactrang')
@login_required
def get_cactrang():
    trang_list = []
    try:
        with open('cactrang.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    name, path = line.split('|', 1)
                    trang_list.append({
                        'name': name.strip(),
                        'path': path.strip()
                    })
    except FileNotFoundError:
        pass
    return jsonify(trang_list)

@app.route('/<path:subpath>')
def serve_subpath(subpath):
    # Kiểm tra nếu là file tĩnh (css, js, images...)
    if subpath.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
        return send_from_directory('.', subpath)
    
    # Kiểm tra session cho các trang HTML trong thư mục con
    if subpath.endswith('.html') or '/' in subpath:
        if not session.get('admin_logged_in'):
            return render_template('trangchu.html'), 401
        
        # Kiểm tra file tồn tại
        if os.path.exists(subpath):
            return send_from_directory('.', subpath)
    
    return render_template('trangchu.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
