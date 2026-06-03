from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
from functools import wraps
import pymysql
from urllib.parse import urlparse
import json
from datetime import datetime
import hashlib

app = Flask(__name__, template_folder='.', static_folder='.')

# Cấu hình session
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chuoi-bi-mat-mac-dinh-khi-chay-local")

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ==================== HÀM KẾT NỐI DATABASE ====================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Fallback local (bạn có thể sửa lại thông số của mình)
        return pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='howiloveyou',
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
    url = urlparse(db_url)
    return pymysql.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path[1:],
        port=url.port or 3306,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

# ==================== DECORATOR LOGIN ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Unauthorized'}), 401
            return render_template('trangchu.html'), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== TRANG CHỦ ====================
@app.route('/')
def index():
    return render_template('trangchu.html')

# ==================== AUTHENTICATION ====================
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

# ==================== API: LẤY DANH SÁCH TOOL TỪ FILE (giữ nguyên) ====================
@app.route('/api/cactrang')
@login_required
def get_cactrang():
    try:
        tools = []
        if os.path.exists('cactrang.txt'):
            with open('cactrang.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        name, path = line.split('|', 1)
                        tools.append({
                            'name': name.strip(),
                            'path': path.strip()
                        })
        return jsonify(tools)
    except Exception as e:
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500

# ==================== API: THỐNG KÊ DASHBOARD ====================
@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Tổng số trang
            cur.execute("SELECT COUNT(*) as total FROM love_pages")
            total_pages = cur.fetchone()['total']
            
            # Tổng lượt xem
            cur.execute("SELECT COALESCE(SUM(views), 0) as total_views FROM love_pages")
            total_views = cur.fetchone()['total_views']
            
            # Top 5 trang xem nhiều nhất
            cur.execute("""
                SELECT title, slug, views 
                FROM love_pages 
                ORDER BY views DESC 
                LIMIT 5
            """)
            top_pages = cur.fetchall()
            
            # Thống kê theo tháng (6 tháng gần nhất)
            cur.execute("""
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as count
                FROM love_pages
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 5 MONTH)
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY month ASC
            """)
            monthly_stats = cur.fetchall()
            
        conn.close()
        
        return jsonify({
            'success': True,
            'total_pages': total_pages,
            'total_views': total_views,
            'top_pages': top_pages,
            'monthly_stats': monthly_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API: QUẢN LÝ TRANG ====================
@app.route('/api/pages')
@login_required
def get_pages():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, slug, title, girl_name, love_message, template_id, views, created_at
                FROM love_pages 
                ORDER BY id DESC
            """)
            pages = cur.fetchall()
        conn.close()
        
        for page in pages:
            page['created_at'] = page['created_at'].strftime('%d/%m/%Y %H:%M') if page['created_at'] else ''
            page['public_url'] = f"/p/{page['slug']}"
            
        return jsonify({'success': True, 'pages': pages})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pages/<int:page_id>', methods=['DELETE'])
@login_required
def delete_page(page_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM love_pages WHERE id = %s", (page_id,))
            conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Đã xóa trang'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pages/<int:page_id>', methods=['PUT'])
@login_required
def update_page(page_id):
    data = request.get_json() or {}
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE love_pages 
                SET title = %s, girl_name = %s, love_message = %s
                WHERE id = %s
            """, (data.get('title'), data.get('girl_name'), data.get('love_message'), page_id))
            conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Đã cập nhật'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API: TẠO TRANG MỚI ====================
@app.route('/api/create-page', methods=['POST'])
@login_required
def create_page():
    data = request.form if request.form else request.get_json() or {}
    
    slug = data.get('slug', '').strip().lower()
    title = data.get('title', '').strip()
    girl_name = data.get('girl_name', '').strip()
    love_message = data.get('love_message', '').strip()
    template_id = data.get('template_id', 'default').strip()
    
    # Xử lý upload ảnh (nếu có file)
    background_image = None
    if 'background_image' in request.files:
        file = request.files['background_image']
        if file and file.filename:
            os.makedirs('uploads/backgrounds', exist_ok=True)
            ext = file.filename.rsplit('.', 1)[-1].lower()
            filename = f"{slug}_{int(datetime.now().timestamp())}.{ext}"
            file.save(f"uploads/backgrounds/{filename}")
            background_image = f"/uploads/backgrounds/{filename}"
    
    # Xử lý upload nhạc
    background_music = data.get('music_url', '').strip()
    if 'background_music' in request.files:
        file = request.files['background_music']
        if file and file.filename:
            os.makedirs('uploads/music', exist_ok=True)
            ext = file.rsplit('.', 1)[-1].lower()
            filename = f"{slug}_{int(datetime.now().timestamp())}.{ext}"
            file.save(f"uploads/music/{filename}")
            background_music = f"/uploads/music/{filename}"
    
    # Hiệu ứng
    effects = json.dumps({
        'heart_rain': data.get('heart_rain') == 'true',
        'confetti': data.get('confetti') == 'true',
        'countdown': data.get('countdown_date') or None
    })
    
    if not slug or not title or not girl_name or not love_message:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Kiểm tra slug
            cur.execute("SELECT id FROM love_pages WHERE slug = %s", (slug,))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Slug này đã tồn tại!'}), 400
            
            sql = """
                INSERT INTO love_pages (slug, title, girl_name, love_message, template_id, 
                                        background_image, background_music, effects)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (slug, title, girl_name, love_message, template_id, 
                             background_image, background_music, effects))
            conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Tạo trang thành công!', 'slug': slug})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API: TEMPLATES ====================
@app.route('/api/templates')
@login_required
def get_templates():
    # Đọc danh sách template từ thư mục templates_mau
    templates = []
    template_dir = 'templates_mau'
    if os.path.exists(template_dir):
        for filename in os.listdir(template_dir):
            if filename.endswith('.html'):
                template_id = filename.replace('.html', '')
                templates.append({
                    'id': template_id,
                    'name': template_id.capitalize(),
                    'description': f'Mẫu {template_id}',
                    'preview': None
                })
    
    # Nếu chưa có template nào, trả về mặc định
    if not templates:
        templates = [
            {'id': 'default', 'name': 'Default', 'description': 'Mẫu mặc định'},
            {'id': 'yesno', 'name': 'Yes/No', 'description': 'Mẫu có nút đồng ý/từ chối'}
        ]
    
    return jsonify({'success': True, 'templates': templates})

@app.route('/api/templates/<template_id>/preview')
def preview_template(template_id):
    return render_template(f"templates_mau/{template_id}.html", data={
        'title': 'Xem trước template',
        'girl_name': 'Người yêu',
        'love_message': 'Đây là bản xem trước của template này'
    })

# ==================== CẬP NHẬT LƯỢT XEM ====================
@app.route('/api/update-views/<slug>', methods=['POST'])
def update_views(slug):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE love_pages SET views = views + 1 WHERE slug = %s", (slug,))
            conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== TRANG PUBLIC (/p/slug) ====================
@app.route('/p/<slug>')
def serve_love_page(slug):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM love_pages WHERE slug = %s", (slug.lower(),))
            page_data = cur.fetchone()
            
            if page_data:
                # Cập nhật lượt xem
                cur.execute("UPDATE love_pages SET views = views + 1 WHERE slug = %s", (slug.lower(),))
                conn.commit()
                
                # Parse effects
                if page_data.get('effects'):
                    page_data['effects'] = json.loads(page_data['effects'])
                else:
                    page_data['effects'] = {'heart_rain': False, 'confetti': False, 'countdown': None}
        conn.close()
        
        if page_data:
            return render_template(f"templates_mau/{page_data['template_id']}.html", data=page_data)
        return render_template('trangchu.html'), 404
    except Exception as e:
        return f"Hệ thống đang bận: {str(e)}", 500

# ==================== ROUTE CHO UPLOAD FILES ====================
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)

# ==================== ROUTE PHÂN PHỐI FILE TĨNH ====================
@app.route('/<path:subpath>')
def serve_subpath(subpath):
    banned_files = ['app.py', 'requirements.txt', '.env', 'wsgi.py']
    
    if subpath in banned_files or '..' in subpath:
        return render_template('trangchu.html'), 403
    
    if subpath in ['trangchu.css', 'trangchu.js']:
        return send_from_directory('.', subpath)
    
    if subpath.endswith('.html'):
        if not session.get('admin_logged_in'):
            return render_template('trangchu.html'), 401
        if os.path.exists(subpath) and os.path.isfile(subpath):
            return send_from_directory('.', subpath)
    
    return render_template('trangchu.html'), 404

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
