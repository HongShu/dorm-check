// API 调用封装
const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('token');
}

function getUser() {
  const u = localStorage.getItem('user');
  return u ? JSON.parse(u) : null;
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API_BASE + path, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    location.href = 'index.html';
    throw new Error('未登录');
  }

  const json = await res.json();
  if (json.code !== 0) {
    throw new Error(json.message || '请求失败');
  }
  return json.data;
}

// 认证
async function login(username, password) {
  const res = await fetch(API_BASE + '/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const json = await res.json();
  if (json.code !== 0) throw new Error(json.message);
  localStorage.setItem('token', json.data.token);
  localStorage.setItem('user', JSON.stringify(json.data));
  return json.data;
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  location.href = 'index.html';
}

// 宿管端
async function getRooms(date) {
  return request(`/checker/rooms?date=${date}`);
}

async function getRoomDetail(room, date) {
  return request(`/checker/rooms/${room}?date=${date}`);
}

async function submitCheck(data) {
  return request('/checker/submit', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

async function finishCheck(date) {
  return request(`/checker/finish?date=${date}`, { method: 'POST' });
}

// 管理员端
async function getDashboard(date) {
  return request(`/admin/dashboard?date=${date}`);
}

async function getAnomalies(date, building, type, counselor) {
  let url = `/admin/anomalies?date=${date}`;
  if (building) url += `&building=${building}`;
  if (type) url += `&type=${type}`;
  if (counselor) url += `&counselor=${counselor}`;
  return request(url);
}

async function getReport(date) {
  return request(`/admin/report?date=${date}`);
}

async function generateReport(date) {
  return request('/admin/report/generate', {
    method: 'POST',
    body: JSON.stringify({ date }),
  });
}

function getToday() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getBuildingName(b) {
  return b + '号楼';
}

// 用户管理
async function getUsers() {
  return request('/admin/users');
}

async function resetCheckerPasswords(newPassword) {
  return request('/admin/reset-checker-passwords', {
    method: 'POST',
    body: JSON.stringify({ new_password: newPassword }),
  });
}
