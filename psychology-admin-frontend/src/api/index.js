// 文件路径: psychology-admin-frontend/src/api/index.js

import axios from 'axios';

// ====================================================================
// --- Axios 实例定义 ---
// 我们创建多个实例来清晰地分离不同API端点的基础路径，便于维护。
// ====================================================================

/**
 * @description Admin 专用实例
 * 所有需要 /api/v1/admin 前缀的后台管理请求都通过它发送。
 */
const adminApi = axios.create({
  baseURL: '/api/v1/admin',
  timeout: 120000, // 设置较长的超时时间，以应对可能耗时较长的AI分析
});

/**
 * @description Auth 专用实例
 * 所有认证相关请求（登录、获取用户信息等）都通过它发送。
 * baseURL 直接指向认证模块，使得调用时路径更简洁。
 */
const authApi = axios.create({
  baseURL: '/api/v1/auth',
  timeout: 120000,
});

/**
 * @description 通用基础实例
 * 用于访问不带特定前缀（如/admin, /auth）的API，或者需要写完整路径的特殊情况。
 */
const baseApi = axios.create({
    baseURL: '/', // 根路径
    timeout: 120000,
});

// ====================================================================
// --- 请求拦截器 ---
// 统一为所有实例添加请求拦截器，自动在请求头中附加认证Token。
// ====================================================================
[adminApi, authApi, baseApi].forEach(apiInstance => {
  apiInstance.interceptors.request.use(
    (config) => {
      // 从 localStorage 中获取管理员token
      const token = localStorage.getItem('admin_token');
      if (token) {
        // 如果token存在，将其添加到 Authorization 请求头中
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      // 对请求错误做些什么
      return Promise.reject(error);
    }
  );
});

// ====================================================================
// --- API 方法导出 ---
// 将所有API请求封装成函数，按模块导出，方便组件调用。
// ====================================================================
export default {
  /**
   * @namespace auth 认证模块
   */
  auth: {
    login(username, password) {
      // OAuth2.0 的密码模式要求使用 application/x-www-form-urlencoded 格式
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      // 使用 authApi 实例，请求的实际URL是: /api/v1/auth/token
      return authApi.post('/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
    },
    getCurrentUser() {
      // 使用 authApi 实例，请求的实际URL是: /api/v1/auth/users/me
      return authApi.get('/users/me');
    }
  },

  /**
   * @namespace users 用户管理模块
   */
  users: {
    getUsers(skip = 0, limit = 100) {
      return adminApi.get(`/users`, { params: { skip, limit } });
    },
    updateUser(userId, userData) {
      return adminApi.patch(`/users/${userId}`, userData);
    },
  },

  /**
   * @namespace stats 数据统计模块
   */
  stats: {
    getDemographicsStats() {
      return adminApi.get('/stats/demographics');
    },
    getAIAnalysis(statsData) {
      return adminApi.post('/stats/ai-analysis', { demographics: statsData });
    }
  },

  /**
   * @namespace assessments 评估记录模块
   */
  assessments: {
    search(idCard = null) {
      const params = {};
      if (idCard) params.id_card = idCard;
      return adminApi.get(`/assessments/search`, { params });
    },
    // 注意：获取单个报告的接口不在/admin下，因此使用通用实例
    getById(assessmentId) {
      return baseApi.get(`/api/v1/reports/${assessmentId}`);
    }
  },

  /**
   * @namespace guidance 指导方案模块
   */
  guidance: {
    getGuidance(scenario, idCard) {
      // `scenario` 可以是 "petitioner", "juvenile", "police"
      return adminApi.get(`/guidance/${scenario}`, { params: { id_card: idCard } });
    }
  },

  /**
   * @namespace interrogation 智能审讯模块
   */
  interrogation: {
    getList({ skip = 0, limit = 10 }) {
      return adminApi.get('/interrogations', { params: { skip, limit } });
    },
    getById(recordId) {
      return adminApi.get(`/interrogations/${recordId}`);
    },
    start(basicInfo) {
      return adminApi.post('/interrogation/start', basicInfo);
    },
    suggestQuestion(recordId, currentQAs) {
      // 根据后端要求的数据格式构建 payload
      const payload = currentQAs.map(qa => ({ q: qa.q, a: qa.a }));
      return adminApi.post(`/interrogation/${recordId}/suggest`, payload);
    },
    save(recordId, recordUpdate) {
      return adminApi.put(`/interrogation/${recordId}`, recordUpdate);
    }
  }
};