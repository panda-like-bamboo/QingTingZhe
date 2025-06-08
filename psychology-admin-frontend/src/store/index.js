import { createStore } from 'vuex';
import api from '../api';
import router from '../router';
import axios from 'axios';

export default createStore({
  state: {
    token: localStorage.getItem('admin_token') || null,
    user: null,
    users: [],
    totalUsers: 0,
    assessments: [],
    stats: null,
    currentGuidance: null,
    currentReport: null,
    interrogationRecord: null,
    interrogationList: {
      records: [],
      total: 0,
    },
    loading: false,
    error: null,
  },
  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      if (token) {
        localStorage.setItem('admin_token', token);
      } else {
        localStorage.removeItem('admin_token');
      }
    },
    SET_USER(state, user) {
      state.user = user;
    },
    SET_USERS(state, { users, total }) {
      state.users = users;
      state.totalUsers = total;
    },
    SET_ASSESSMENTS(state, assessments) {
      state.assessments = assessments;
    },
    SET_STATS(state, stats) {
        state.stats = stats;
    },
    SET_CURRENT_GUIDANCE(state, guidanceData) {
        state.currentGuidance = guidanceData;
    },
    SET_CURRENT_REPORT(state, reportData) {
        state.currentReport = reportData;
    },
    SET_INTERROGATION_RECORD(state, record) {
        state.interrogationRecord = record;
    },
    SET_INTERROGATION_LIST(state, { records, total }) {
      state.interrogationList.records = records;
      state.interrogationList.total = total;
    },
    UPDATE_INTERROGATION_QA(state, newQAs) {
        if (state.interrogationRecord) {
            state.interrogationRecord.qas = newQAs;
        }
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    CLEAR_ERROR(state) {
      state.error = null;
    },
  },
  actions: {
    async login({ commit }, credentials) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      try {
        const { data } = await api.auth.login(credentials.username, credentials.password);
        commit('SET_TOKEN', data.access_token);
        const userResponse = await api.auth.getCurrentUser();
        if (!userResponse.data.is_superuser) {
            throw new Error('您不是管理员，无法登录后台系统。');
        }
        commit('SET_USER', userResponse.data);
        router.push({ name: 'Dashboard' });
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '登录失败';
        commit('SET_ERROR', errorMessage);
        commit('SET_TOKEN', null);
        commit('SET_USER', null);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    logout({ commit }) {
      commit('SET_TOKEN', null);
      commit('SET_USER', null);
      router.push({ name: 'Login' });
    },
    async fetchUsers({ commit }, { skip, limit }) {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        try {
            const { data } = await api.users.getUsers(skip, limit);
            commit('SET_USERS', { users: data.users, total: data.total });
        } catch (error) {
            commit('SET_ERROR', '获取用户列表失败');
        } finally {
            commit('SET_LOADING', false);
        }
    },
    async updateUserStatus({ commit }, { userId, isActive }) {
        try {
            await api.users.updateUser(userId, { is_active: isActive });
        } catch (error) {
            const errorMessage = error.response?.data?.detail || '更新用户状态失败';
            commit('SET_ERROR', errorMessage);
            throw new Error(errorMessage);
        }
    },
    async fetchStats({ commit }) {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        try {
            const { data } = await api.stats.getDemographicsStats();
            commit('SET_STATS', data);
        } catch(error) {
            commit('SET_ERROR', '获取统计数据失败');
        } finally {
            commit('SET_LOADING', false);
        }
    },
    async searchAssessments({ commit }, idCard) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      commit('SET_ASSESSMENTS', []);
      try {
        const { data } = await api.assessments.search(idCard);
        commit('SET_ASSESSMENTS', data);
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '搜索评估记录失败';
        commit('SET_ERROR', errorMessage);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchGuidance({ commit }, { scenario, idCard }) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      commit('SET_CURRENT_GUIDANCE', null);
      try {
        const { data } = await api.guidance.getGuidance(scenario, idCard);
        commit('SET_CURRENT_GUIDANCE', data);
        return data; // <<< FIX: Return the fetched data
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '获取指导方案失败';
        commit('SET_ERROR', errorMessage);
        throw new Error(errorMessage);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchReportById({ commit }, assessmentId) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      commit('SET_CURRENT_REPORT', null);
      try {
        const { data } = await api.assessments.getById(assessmentId);
        if (data && data.report) {
          commit('SET_CURRENT_REPORT', data.report);
        } else if (data && data.message) {
          throw new Error(data.message);
        } else {
          throw new Error('获取报告时返回了无效的数据格式');
        }
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '获取报告详情失败';
        commit('SET_ERROR', errorMessage);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async startInterrogation({ commit }, basicInfo) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      try {
        const { data } = await api.interrogation.start(basicInfo);
        commit('SET_INTERROGATION_RECORD', data);
        return data;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '开始新的审讯失败';
        commit('SET_ERROR', errorMessage);
        throw new Error(errorMessage);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async suggestQuestion({ commit }, { recordId, currentQAs }) {
      try {
        const { data } = await api.interrogation.suggestQuestion(recordId, currentQAs);
        return data;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '获取AI建议失败';
        commit('SET_ERROR', errorMessage);
        throw new Error(errorMessage);
      }
    },
    async saveInterrogation({ commit }, { recordId, updateData }) {
      if (!recordId) {
        throw new Error('没有可保存的审讯记录ID');
      }
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      try {
        const { data } = await api.interrogation.save(recordId, updateData);
        // 保存成功后，更新当前的 interrogationRecord
        commit('SET_INTERROGATION_RECORD', data);
        return data;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '保存审讯笔录失败';
        commit('SET_ERROR', errorMessage);
        throw new Error(errorMessage);
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async fetchInterrogationRecordById({ commit }, recordId) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      commit('SET_INTERROGATION_RECORD', null);
      try {
        const { data } = await api.interrogation.getById(recordId);
        commit('SET_INTERROGATION_RECORD', data);
        return data;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || `获取审讯记录(ID: ${recordId})失败`;
        commit('SET_ERROR', errorMessage);
        throw new Error(errorMessage);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchInterrogationList({ commit }, { skip, limit }) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      try {
        const { data } = await api.interrogation.getList({ skip, limit });
        commit('SET_INTERROGATION_LIST', {
          records: data.records,
          total: data.total,
        });
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '获取审讯记录列表失败';
        commit('SET_ERROR', errorMessage);
        commit('SET_INTERROGATION_LIST', { records: [], total: 0 });
      } finally {
        commit('SET_LOADING', false);
      }
    },
  },
});