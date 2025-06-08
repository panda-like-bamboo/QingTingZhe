// 文件路径: psychology-app-new/src/api/index.js (最终修复版)

import axios from 'axios';

// 创建 axios 实例，配置基础 URL 和超时时间
const api = axios.create({
  baseURL: '/api/v1', // 基础路径
  timeout: 120000, 
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- 认证相关的 API 函数 ---
export const authAPI = {
  login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    // 登录接口路径是正确的：/api/v1 + /auth/token
    return api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },

  register(userData) {
    // 注册接口路径是 /api/v1 + /auth/register
    return api.post('/auth/register', userData, {
      headers: { 'Content-Type': 'application/json' }
    });
  },

  // [->] 核心修复：修改获取用户信息的路径
  getCurrentUser() {
    // 将请求路径从 /users/me 改为 /auth/users/me，
    // 这样拼接上 baseURL /api/v1 后，
    // 最终请求的URL就是正确的 /api/v1/auth/users/me
    return api.get('/auth/users/me'); 
  }
};

// --- 其他 API 模块 (保持不变) ---
export const scalesAPI = {
  getAvailableScales() { return api.get('/scales'); },
  getScaleQuestions(scaleCode) { return api.get(`/scales/${scaleCode}/questions`); }
};

export const encyclopediaAPI = {
  getCategories() { return api.get('/encyclopedia/categories'); },
  getEntries(category = null) {
    const url = category
      ? `/encyclopedia/entries?category=${encodeURIComponent(category)}`
      : '/encyclopedia/entries';
    return api.get(url);
  },
  getRandomTip() { return api.get('/encyclopedia/entries?random_tip=true'); }
};

export const assessmentsAPI = {
  submitAssessment(formData) {
    return api.post('/assessments/submit', formData);
  }
};

export const reportsAPI = {
  getReport(assessmentId) { return api.get(`/reports/${assessmentId}`); },
  getReportStatus(assessmentId) { return api.get(`/reports/${assessmentId}/status`); }
};

// 统一导出所有 API 模块
export default {
  auth: authAPI,
  scales: scalesAPI,
  encyclopedia: encyclopediaAPI,
  assessments: assessmentsAPI,
  reports: reportsAPI
};