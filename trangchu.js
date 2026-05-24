// trangchu.js
let isLoggedIn = false;

// Kiểm tra session khi load trang
async function checkSession() {
    try {
        const response = await fetch('/api/cactrang');
        if (response.ok) {
            isLoggedIn = true;
            showDashboard();
            await loadTools();
        } else {
            showLogin();
        }
    } catch (error) {
        showLogin();
    }
}

// Hiển thị form login
function showLogin() {
    document.getElementById('loginContainer').classList.remove('hidden');
    document.getElementById('dashboardContainer').classList.add('hidden');
    isLoggedIn = false;
}

// Hiển thị dashboard
function showDashboard() {
    document.getElementById('loginContainer').classList.add('hidden');
    document.getElementById('dashboardContainer').classList.remove('hidden');
    isLoggedIn = true;
}

// Load danh sách công cụ từ API
async function loadTools() {
    try {
        const response = await fetch('/api/cactrang');
        const tools = await response.json();
        
        const toolsGrid = document.getElementById('toolsGrid');
        
        if (tools.length === 0) {
            toolsGrid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="ri-tools-line text-6xl text-gray-400 mb-4"></i>
                    <p class="text-gray-400 text-lg">Chưa có công cụ nào. Thêm vào file cactrang.txt nhé!</p>
                </div>
            `;
            return;
        }
        
        toolsGrid.innerHTML = tools.map((tool, index) => `
            <div class="card-animate bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300 hover:scale-105 cursor-pointer group" style="animation-delay: ${index * 0.1}s" onclick="window.location.href='/${tool.path}'">
                <div class="flex items-start justify-between mb-4">
                    <i class="ri-tools-line text-4xl text-purple-400 group-hover:rotate-12 transition-transform duration-300"></i>
                    <i class="ri-arrow-right-up-line text-2xl text-gray-400 group-hover:text-white group-hover:translate-x-1 group-hover:-translate-y-1 transition-all"></i>
                </div>
                <h3 class="text-xl font-bold text-white mb-2">${escapeHtml(tool.name)}</h3>
                <p class="text-gray-300 text-sm">Đường dẫn: /${tool.path}</p>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Lỗi tải công cụ:', error);
        showToast('Không thể tải danh sách công cụ', 'error');
    }
}

// Xử lý đăng nhập
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showToast('Vui lòng nhập đầy đủ thông tin', 'error');
        return;
    }
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Đăng nhập thành công!', 'success');
            isLoggedIn = true;
            showDashboard();
            await loadTools();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối đến server', 'error');
    }
});

// Xử lý đăng xuất
document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    try {
        await fetch('/logout', { method: 'POST' });
        showToast('Đã đăng xuất', 'success');
        showLogin();
    } catch (error) {
        showToast('Lỗi khi đăng xuất', 'error');
    }
});

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-xl shadow-lg z-50 animate-fade-in ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    toast.innerHTML = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Escape HTML để tránh XSS
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Khởi tạo
checkSession();
