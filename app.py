from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
from functools import wraps
import pymysql
from urllib.parse import urlparse

app = Flask(__name__, template_folder='.', static_folder='.')

# 1. FIX LỖI COOKIE VÀ SESSION TRÊN CLOUD
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chuoi-bi-mat-mac-dinh-khi-chay-local") [cite: 19]

ADMIN_USERNAME = 'admin' [cite: 21]
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123") [cite: 22]

# 2. HÀM KẾT NỐI DATABASE MYSQL QUA BIẾN MÔI TRƯỜNG NỘI BỘ (DATABASE_URL)
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("Chưa cấu hình biến môi trường DATABASE_URL!")
    
    url = urlparse(db_url)
    return pymysql.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path[1:],  # Bỏ dấu gạch chéo '/' ở đầu tên database
        port=url.port or 3306,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

def login_required(f): [cite: 23]
    @wraps(f) [cite: 24]
    def decorated_function(*args, **kwargs): [cite: 25]
        if not session.get('admin_logged_in'): [cite: 26]
            return jsonify({'error': 'Unauthorized'}), 401 [cite: 27]
        return f(*args, **kwargs) [cite: 28]
    return decorated_function [cite: 29]

@app.route('/') [cite: 30]
def index(): [cite: 31]
    return render_template('trangchu.html') [cite: 32]

@app.route('/login', methods=['POST']) [cite: 33]
def login(): [cite: 34]
    data = request.get_json() or {} [cite: 35]
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD: [cite: 36]
        session['admin_logged_in'] = True [cite: 37]
        return jsonify({'success': True, 'message': 'Đăng nhập thành công'}) [cite: 38]
    return jsonify({'success': False, 'message': 'Sai tài khoản hoặc mật khẩu'}), 401 [cite: 39]

@app.route('/logout', methods=['POST']) [cite: 40]
def logout(): [cite: 41]
    session.pop('admin_logged_in', None) [cite: 42]
    return jsonify({'success': True, 'message': 'Đã đăng xuất'}) [cite: 43]

# 3. LẤY DANH SÁCH TRANG TỪ DATABASE ĐỂ ĐỔ RA DASHBOARD (Thay thế file cactrang.txt cũ)
@app.route('/api/cactrang') [cite: 44]
@login_required [cite: 45]
def get_cactrang(): [cite: 46]
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT title AS name, CONCAT('p/', slug) AS path FROM love_pages ORDER BY id DESC")
            trang_list = cur.fetchall()
        conn.close()
        return jsonify(trang_list) # Giữ đúng định dạng JSON cũ để frontend không bị lỗi [cite: 55, 56, 57, 58]
    except Exception as e:
        return jsonify({'error': f'Lỗi database: {str(e)}'}), 500

# 4. API TẠO TRANG MỚI CHO ADMIN (Ghi trực tiếp vào MySQL)
@app.route('/api/taotrang', methods=['POST'])
@login_required
def create_page():
    data = request.get_json() or {}
    slug = data.get('slug', '').strip().lower()
    title = data.get('title', '').strip()
    girl_name = data.get('girl_name', '').strip()
    love_message = data.get('love_message', '').strip()
    template_id = data.get('template_id', 'default').strip()

    if not slug or not title or not girl_name or not love_message:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Kiểm tra xem link slug này đã có ông nào xài chưa
            cur.execute("SELECT id FROM love_pages WHERE slug = %s", (slug,))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Đường link (Slug) này đã tồn tại!'}), 400
            
            # Tiến hành chèn dữ liệu
            sql = """INSERT INTO love_pages (slug, title, girl_name, love_message, template_id) 
                     VALUES (%s, %s, %s, %s, %s)"""
            cur.execute(sql, (slug, title, girl_name, love_message, template_id))
            conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Tạo trang tỏ tình thành công!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

# 5. ROUTE ĐỘNG PUBLIC PHỤC VỤ TRANG TỎ TÌNH CỦA BẠN NỮ (/p/slug)
@app.route('/p/<slug>')
def serve_love_page(slug):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM love_pages WHERE slug = %s", (slug.lower(),))
            page_data = cur.fetchone()
        conn.close()

        if page_data:
            # Render ra giao diện mẫu tương ứng và truyền cục dữ liệu 'data' vào file HTML
            # Ông cần tạo sẵn thư mục 'templates_mau' và chứa các mẫu trong đó (ví dụ: default.html, yesno.html)
            return render_template(f"templates_mau/{page_data['template_id']}.html", data=page_data)
        
        return render_template('trangchu.html'), 404
    except Exception as e:
        return f"Hệ thống Database đang bận: {str(e)}", 500

# 6. ROUTE PHÂN PHỐI FILE TĨNH GỐC VÀ BẢO MẬT HỆ THỐNG
@app.route('/<path:subpath>') [cite: 62]
def serve_subpath(subpath): [cite: 63]
    banned_files = ['app.py', 'requirements.txt', '.env', 'wsgi.py'] [cite: 67]
    if subpath in banned_files or '..' in subpath: [cite: 68]
        return render_template('trangchu.html'), 403 [cite: 69]

    if subpath in ['trangchu.css', 'trangchu.js']: [cite: 71]
        return send_from_directory('.', subpath) [cite: 72]

    # Các file giao diện HTML con trong thư mục tĩnh bắt buộc phải đăng nhập [cite: 75]
    if '/' in subpath or subpath.endswith('.html'): [cite: 75]
        if not session.get('admin_logged_in'): [cite: 76]
            return render_template('trangchu.html'), 401 [cite: 77]

    if os.path.exists(subpath) and os.path.isfile(subpath): [cite: 79]
        return send_from_directory('.', subpath) [cite: 80]

    return render_template('trangchu.html'), 404 [cite: 81]

if __name__ == '__main__': [cite: 83]
    port = int(os.environ.get("PORT", 5000)) [cite: 84]
    app.run(host="0.0.0.0", port=port, debug=False) [cite: 85]
