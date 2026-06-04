// trangchu.js
let isLoggedIn = false;
let toastId = 0;

// Toast System
function showToast(message, type = 'success', title = null) {
  // Kiểm tra container đã tồn tại chưa
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
      position: fixed;
      bottom: 30px;
      right: 30px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 12px;
    `;
    document.body.appendChild(container);
  }

  const id = toastId++;
  const titles = {
    success: 'Thành công!',
    error: 'Lỗi!',
    warning: 'Cảnh báo!',
    info: 'Thông báo'
  };

  const finalTitle = title || titles[type] || 'Thông báo';
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };

  const borderColors = {
    success: '#22c55e',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  };

  const toast = document.createElement('div');
  toast.className = 'toast-item';
  toast.style.cssText = `
    background: #1e1e2e;
    border-radius: 12px;
    padding: 14px 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 320px;
    border-left: 5px solid ${borderColors[type]};
    transform: translateX(400px);
    opacity: 0;
    transition: all 0.3s ease;
  `;
  
  toast.innerHTML = `
    <div class="toast-icon" style="width: 28px; height: 28px; background: ${borderColors[type]}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold; flex-shrink: 0; color: white;">${icons[type] || '✓'}</div>
    <div class="toast-content" style="flex: 1;">
      <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: #fff;">${finalTitle}</h4>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #a1a1aa;">${message}</p>
    </div>
    <button class="toast-close" style="background: none; border: none; color: #666; cursor: pointer; font-size: 18px; padding: 0 4px;">×</button>
  `;

  container.appendChild(toast);
  
  // Animation hiện
  setTimeout(() => {
    toast.style.transform = 'translateX(0)';
    toast.style.opacity = '1';
  }, 10);

  // Xử lý nút đóng
  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.onclick = () => {
    toast.style.transform = 'translateX(400px)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  };

  // Tự động ẩn sau 4 giây
  setTimeout(() => {
    if (toast && toast.parentNode) {
      toast.style.transform = 'translateX(400px)';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }
  }, 4000);
}

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
    
    if (!toolsGrid) return;
    
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
    showToast('Vui lòng nhập đầy đủ thông tin', 'warning');
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
    showToast('Đã đăng xuất', 'info');
    showLogin();
  } catch (error) {
    showToast('Lỗi khi đăng xuất', 'error');
  }
});

// Escape HTML để tránh XSS
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Khởi tạo
checkSession();
