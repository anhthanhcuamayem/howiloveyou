from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
from functools import wraps

app = Flask(__name__, template_folder='.', static_folder='.')

# 1. FIX LỖI CHẾT SESSION TRÊN RENDER: 
# os.urandom(24) sẽ đổi key mỗi lần Render tự restart ứng dụng, làm Admin bị văng login liên tục.
# Dùng os.environ giúp giữ phiên đăng nhập ổn định.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chuoi-bi-mat-mac-dinh-khi-chay-local")

# 2. BẢO MẬT BIẾN MÔI TRƯỜNG:
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123") # Mặc định local là admin123

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
    data = request.get_json() or {}
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
        if os.path.exists('cactrang.txt'):
            with open('cactrang.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        name, path = line.split('|', 1)
                        trang_list.append({
                            'name': name.strip(),
                            'path': path.strip()
                        })
    except Exception as e:
        return jsonify({'error': 'Không thể đọc file dữ liệu'}), 500
    return jsonify(trang_list)

@app.route('/<path:subpath>')
def serve_subpath(subpath):
    # 3. VÁ LỖI BẢO MẬT NGUY HIỂM (Path Traversal Fix):
    # Code cũ của DS cho phép người dùng gõ link mò ngược ra đọc file hệ thống (Ví dụ: /app.py hoặc /cactrang.txt)
    # Chặn không cho truy cập trực tiếp các file code, cấu hình, dữ liệu cốt lõi ở thư mục gốc
    banned_files = ['app.py', 'requirements.txt', 'cactrang.txt', '.env', 'wsgi.py']
    if subpath in banned_files or '..' in subpath:
        return render_template('trangchu.html'), 403

    # Kiểm tra nếu là file tĩnh đi kèm của trang chủ (nằm ở gốc)
    if subpath in ['trangchu.css', 'trangchu.js']:
        return send_from_directory('.', subpath)

    # 4. CHẶN ROUTE ĐỘNG CHO CÁC THƯ MỤC CON:
    # Nếu truy cập vào thư mục con hoặc file html bên trong, BẮT BUỘC phải đăng nhập
    if '/' in subpath or subpath.endswith('.html'):
        if not session.get('admin_logged_in'):
            return render_template('trangchu.html'), 401
        
        # Ngăn chặn việc gửi file không tồn tại gây sập app
        if os.path.exists(subpath) and os.path.isfile(subpath):
            return send_from_directory('.', subpath)
        
    return render_template('trangchu.html'), 404

# 5. CẤU HÌNH CỔNG PORT LINH HOẠT CHO RENDER
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
