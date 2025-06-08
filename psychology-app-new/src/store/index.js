// src/store/index.js
import { createStore } from 'vuex';
import api from '../api'; // 确保 api 导入正确

const store = createStore({
  state() {
    // 定义 Vuex store 的初始状态
    return {
      user: null, // 当前登录用户信息
      // --- 关键修改：不再从 localStorage 初始化 token ---
      token: null, // 用户认证令牌，初始为 null，不再从 localStorage 读取
      // ----------------------------------------------
      scales: [], // 可用量表列表
      currentScale: null, // 当前选择的量表代码
      scaleQuestions: [], // 当前量表的问题列表
      assessment: { // 评估相关数据
        basicInfo: { // 用户填写的基本信息
          name: '',
          gender: '',
          age: '',
          id_card: '',
          occupation: '',
          case_name: '',
          case_type: '',
          identity_type: '',
          person_type: '',
          marital_status: '',
          children_info: '',
          criminal_record: 0, // 保持数字类型，0 代表无
          health_status: '',
          phone_number: '',
          domicile: '',
        },
        answers: {}, // 用户对量表问题的回答
        uploadedImage: null, // 用户上传的图片文件
        submissionId: null // 提交评估后获取的 ID
      },
      psychologyTips: [], // 心理小贴士列表 (似乎未使用，但保留)
      currentTip: null, // 当前显示的心理小贴士
      loading: false, // 全局加载状态标志
      error: null, // 全局错误信息
      report: null ,// 存储获取到的分析报告数据
      reportStatus: 'pending', // 可能的状态: 'pending', 'processing', 'complete', 'failed', 'not_found'
    };
  },

  getters: {
    // 定义基于 state 的计算属性
    // isAuthenticated 仍然依赖 state.token，现在初始值将为 false
    isAuthenticated(state) {
      // 判断用户是否已认证（是否有 token）
      return !!state.token;
    },
    currentUser(state) {
      // 获取当前用户信息
      return state.user;
    },
    availableScales(state) {
      // 获取可用量表列表
      return state.scales;
    },
    getScaleQuestions(state) {
      // 获取当前量表的问题
      return state.scaleQuestions;
    },
    getCurrentTip(state) {
      // 获取当前显示的心理小贴士
      return state.currentTip;
    },
    getAssessmentBasicInfo(state) {
      // 获取评估的基本信息
      return state.assessment.basicInfo;
    },
    getAssessmentAnswers(state) {
      // 获取评估的答案
      return state.assessment.answers;
    },
    getUploadedImage(state) {
      // 获取上传的图片
      return state.assessment.uploadedImage;
    },
    getSubmissionId(state) {
      // 获取提交 ID
      console.log('[Getter: getSubmissionId] 返回:', state.assessment.submissionId);
      return state.assessment.submissionId;
    },
    getReport(state) {
      // 获取分析报告
      console.log('[Getter: getReport] 返回:', state.report);
      return state.report;
    },
    isLoading(state) {
      // 获取加载状态
      return state.loading;
    },
    getReportStatus(state) {
       return state.reportStatus; 
    },
  },

  mutations: {
    // 定义同步修改 state 的方法
    SET_TOKEN(state, token) {
      // 设置认证 Token
      state.token = token;
      // --- 保留将 token 写入 localStorage 的逻辑 ---
      // 这仍然有用，比如可以在开发者工具中查看当前 token，
      // 但它不会影响下次启动时的自动登录了。
      if (token) {
        localStorage.setItem('token', token);
        console.log('[Mutation: SET_TOKEN] Token 已设置到 state 和 localStorage。');
      } else {
        localStorage.removeItem('token');
        console.log('[Mutation: SET_TOKEN] Token 已从 state 和 localStorage 移除。');
      }
      // ---------------------------------------------
    },
    SET_USER(state, user) {
      // 设置用户信息
      state.user = user;
      console.log('[Mutation: SET_USER] 用户信息已设置到 state:', user);
    },
    SET_SCALES(state, scales) {
      // 设置量表列表
      state.scales = scales;
      console.log('[Mutation: SET_SCALES] 量表列表已设置到 state:', scales?.length);
    },
    SET_CURRENT_SCALE(state, scaleCode) {
      // 设置当前量表代码
      state.currentScale = scaleCode;
      console.log('[Mutation: SET_CURRENT_SCALE] 当前量表已设置为:', scaleCode);
    },
    SET_SCALE_QUESTIONS(state, questions) {
      // 设置量表问题
      state.scaleQuestions = questions;
       console.log('[Mutation: SET_SCALE_QUESTIONS] 量表问题已设置:', questions?.length);
    },
    SET_PSYCHOLOGY_TIPS(state, tips) {
      // 设置心理小贴士列表
      state.psychologyTips = tips;
       console.log('[Mutation: SET_PSYCHOLOGY_TIPS] 心理小贴士已设置:', tips?.length);
    },
    SET_CURRENT_TIP(state, tip) {
      // 设置当前心理小贴士
      state.currentTip = tip;
       console.log('[Mutation: SET_CURRENT_TIP] 当前心理小贴士已设置:', tip?.title);
    },
    SET_BASIC_INFO(state, info) {
      // 更新基础信息
      state.assessment.basicInfo = { ...state.assessment.basicInfo, ...info };
      console.log('[Mutation: SET_BASIC_INFO] 基础信息已更新。');
    },
    SET_ANSWER(state, { questionNumber, answer }) {
      // 设置单个问题的答案
      state.assessment.answers = {
        ...state.assessment.answers,
        ['q' + questionNumber]: answer // 使用 'q' + 题号 作为 key
      };
      // console.log(`[Mutation: SET_ANSWER] 问题 Q${questionNumber} 的答案已设置为: ${answer}`); // 这个日志比较频繁，可以选择性注释掉
    },
    SET_UPLOADED_IMAGE(state, imageFile) {
      // 设置上传的图片文件
      state.assessment.uploadedImage = imageFile;
      console.log('[Mutation: SET_UPLOADED_IMAGE] 上传的图片已更新:', imageFile ? imageFile.name : null);
    },
    SET_SUBMISSION_ID(state, id) {
      // 设置提交 ID
      state.assessment.submissionId = id;
      console.log('[Mutation: SET_SUBMISSION_ID] 提交 ID 已设置为:', id);
    },
    SET_REPORT(state, report) {
      // 设置分析报告数据
      console.log('[Mutation: SET_REPORT] 触发。接收到的 payload:', report);
      state.report = report;
      if (report && typeof report === 'object' && report.report_text) {
         console.log('[Mutation: SET_REPORT] State 已使用有效的报告数据更新。');
      } else if (report === null || report === undefined) {
         console.log('[Mutation: SET_REPORT] State 已使用 NULL/UNDEFINED 报告更新。');
      } else {
         console.warn('[Mutation: SET_REPORT] State 已更新，但接收到的报告数据似乎无效或不完整:', report);
      }
    },
    SET_REPORT_STATUS(state, status) {
      console.log(`[Mutation: SET_REPORT_STATUS] 状态更新为: ${status}`);
      state.reportStatus = status;
    },
    SET_LOADING(state, isLoading) {
      // 设置加载状态
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      // 设置错误信息
      state.error = error;
      console.error('[Mutation: SET_ERROR] 错误信息已设置到 state:', error);
    },
    RESET_ASSESSMENT(state) {
      // 重置评估相关的状态
      console.log('[Mutation: RESET_ASSESSMENT] 正在重置评估状态...');
      state.assessment = {
        basicInfo: {
          name: '', gender: '', age: '', id_card: '', occupation: '',
          case_name: '', case_type: '', identity_type: '', person_type: '',
          marital_status: '', children_info: '', criminal_record: 0,
          health_status: '', phone_number: '', domicile: '',
        },
        answers: {},
        uploadedImage: null,
        submissionId: null
      };
      state.scaleQuestions = [];
      state.currentScale = null;
      state.report = null; // 同时清空报告
      console.log('[Mutation: RESET_ASSESSMENT] 评估状态重置完成。');
    },
    CLEAR_ERROR(state) {
      // 清除错误信息
      if (state.error) {
        console.log('[Mutation: CLEAR_ERROR] 正在清除错误状态。');
        state.error = null;
      }
    }
  },

  actions: {
    // 定义异步操作或包含业务逻辑的方法

    // --- 身份认证 actions ---
    async login({ commit, dispatch }, { username, password }) {
      // 用户登录
      console.log('[Action: login] 触发。');
      commit('CLEAR_ERROR'); // 清除之前的错误
      commit('SET_LOADING', true); // 开始加载
      try {
        console.log('[Action: login] 尝试 API 登录，用户名:', username);
        const response = await api.auth.login(username, password); // 调用 API
        console.log('[Action: login] 收到 API 响应:', response);
        if (response && response.data && response.data.access_token) {
          // 登录成功
          commit('SET_TOKEN', response.data.access_token); // 保存 token
          await dispatch('fetchCurrentUser'); // 获取当前用户信息
          console.log('[Action: login] 登录并获取用户信息成功。');
          commit('SET_LOADING', false); // 结束加载
          return response; // 返回响应给调用者
        } else {
          // API 响应无效
          throw new Error('登录响应无效或缺少 access_token。');
        }
      } catch (error) {
        // 登录失败
        const errorMessage = error.response?.data?.detail || error.message || '登录失败，请检查您的凭据或网络连接。';
        console.error('[Action: login] 失败。', error.response || error);
        commit('SET_ERROR', errorMessage); // 设置错误信息
        commit('SET_TOKEN', null); // 清除 token
        commit('SET_USER', null); // 清除用户信息
        commit('SET_LOADING', false); // 结束加载
        throw error; // 将错误继续抛出，方便 UI 处理
      }
    },

    async register({ commit }, userData) {
      // 用户注册
      console.log('[Action: register] 触发。');
      commit('CLEAR_ERROR');
      commit('SET_LOADING', true);
      try {
        const response = await api.auth.register(userData); // 调用注册 API
        console.log('[Action: register] API 响应:', response);
        commit('SET_LOADING', false);
        return response; // 返回响应
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '注册失败，请稍后再试。';
        console.error('[Action: register] 失败。', error.response || error);
        commit('SET_ERROR', errorMessage);
        commit('SET_LOADING', false);
        throw error;
      }
    },

    async fetchCurrentUser({ commit, state }) {
      // 获取当前登录用户信息
      console.log('[Action: fetchCurrentUser] 触发。');
      if (!state.token) {
        // 如果没有 token，则无需调用 API
        console.warn('[Action: fetchCurrentUser] 未找到 token，跳过 API 调用。');
        return;
      }
      try {
        const response = await api.auth.getCurrentUser(); // 调用获取用户信息的 API
        console.log('[Action: fetchCurrentUser] API 响应:', response);
        commit('SET_USER', response.data); // 保存用户信息
        return response;
      } catch (error) {
        // 获取失败，可能是 token 失效
        const errorMessage = error.response?.data?.detail || error.message || '无法获取用户信息，您的会话可能已过期。';
        console.error('[Action: fetchCurrentUser] 失败。', error.response || error);
        commit('SET_TOKEN', null); // 清除无效 token
        commit('SET_USER', null); // 清除用户信息
        commit('SET_ERROR', errorMessage); // 设置错误
        // 这里可以选择性地不 throw error，或者根据需要处理
        // throw error;
      }
    },

    logout({ commit }) {
      // 用户登出
      console.log('[Action: logout] 触发。');
      commit('SET_TOKEN', null); // 清除 token
      commit('SET_USER', null); // 清除用户信息
      commit('RESET_ASSESSMENT'); // 重置评估状态
      commit('CLEAR_ERROR'); // 清除错误
      // 可以选择性地调用 API 通知后端登出
      // await api.auth.logout();
      console.log('[Action: logout] 用户已登出，状态已重置。');
    },

    // --- 量表 actions ---
    async fetchScales({ commit }) {
      // 获取可用量表列表
      console.log('[Action: fetchScales] 触发。');
      commit('CLEAR_ERROR');
      commit('SET_LOADING', true);
      try {
        const response = await api.scales.getAvailableScales(); // 调用 API
        console.log('[Action: fetchScales] API 响应:', response.data);
        if (response && response.data && Array.isArray(response.data.scales)) {
            // 检查响应结构是否正确
            commit('SET_SCALES', response.data.scales); // 保存量表列表
        } else {
            console.warn('[Action: fetchScales] 从 API 收到的响应结构无效。');
            commit('SET_SCALES', []); // 设置为空数组
        }
        commit('SET_LOADING', false);
        return response;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '无法加载量表列表。';
        console.error('[Action: fetchScales] 失败。', error.response || error);
        commit('SET_ERROR', errorMessage);
        commit('SET_SCALES', []); // 失败时设置为空数组
        commit('SET_LOADING', false);
        throw error;
      }
    },

    async fetchScaleQuestions({ commit }, scaleCode) {
      // 根据量表代码获取问题列表
      console.log('[Action: fetchScaleQuestions] 触发，量表代码:', scaleCode);
      commit('CLEAR_ERROR');
      commit('SET_LOADING', true);
      try {
        commit('SET_CURRENT_SCALE', scaleCode); // 设置当前量表
        const response = await api.scales.getScaleQuestions(scaleCode); // 调用 API
        console.log('[Action: fetchScaleQuestions] 量表', scaleCode, '的 API 响应:', response.data);
         if (response && response.data && Array.isArray(response.data.questions)) {
            // 检查响应结构
            commit('SET_SCALE_QUESTIONS', response.data.questions); // 保存问题列表
         } else {
            console.warn('[Action: fetchScaleQuestions] 从 API 收到的响应结构无效。');
            commit('SET_SCALE_QUESTIONS', []); // 设置为空数组
         }
        commit('SET_LOADING', false);
        return response;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '无法加载量表问题。';
        console.error('[Action: fetchScaleQuestions] 失败。', error.response || error);
        commit('SET_ERROR', errorMessage);
        commit('SET_SCALE_QUESTIONS', []); // 失败时设置为空数组
        commit('SET_LOADING', false);
        throw error;
      }
    },

    // --- 评估 actions ---
    setBasicInfo({ commit }, info) {
      // 设置评估的基础信息 (这是一个同步操作，理论上可以直接 commit，放在 action 里是为了结构统一)
      console.log('[Action: setBasicInfo] 触发。');
      commit('SET_BASIC_INFO', info);
    },

    setAnswer({ commit }, { questionNumber, answer }) {
      // 设置问题的答案 (同上，同步操作)
      commit('SET_ANSWER', { questionNumber, answer });
    },

    setUploadedImage({ commit }, imageFile) {
      // 设置上传的图片 (同上，同步操作)
       console.log('[Action: setUploadedImage] 触发。');
      commit('SET_UPLOADED_IMAGE', imageFile);
    },

    async submitAssessment({ commit, state }) {
      // 提交评估数据
      console.log('[Action: submitAssessment] 触发。');
      commit('CLEAR_ERROR');
      commit('SET_LOADING', true);
      try {
        // 创建 FormData 对象来发送数据，特别是因为包含文件上传
        const formData = new FormData();

        // 添加基础信息
        Object.entries(state.assessment.basicInfo).forEach(([key, value]) => {
          // 确保不添加 null, undefined 或空字符串的值，除非后端需要
          if (value !== null && value !== undefined && value !== '') {
            formData.append(key, value);
          }
        });

        // 添加量表类型
        if (state.currentScale) {
          formData.append('scale_type', state.currentScale);
        }

        // 添加答案
        Object.entries(state.assessment.answers).forEach(([key, value]) => {
          formData.append(key, value);
        });

        // 添加图片文件（如果存在）
        if (state.assessment.uploadedImage) {
          formData.append('image', state.assessment.uploadedImage);
        }

        console.log('[Action: submitAssessment] 正在向 API 发送 FormData...');
        // 调用提交评估的 API
        const response = await api.assessments.submitAssessment(formData);
        console.log('[Action: submitAssessment] API 响应:', response);

        // 检查响应是否包含 submission_id
        if (response && response.data && response.data.submission_id) {
             commit('SET_SUBMISSION_ID', response.data.submission_id); // 保存提交 ID
        } else {
             console.warn('[Action: submitAssessment] API 响应缺少 submission_id。');
             // 可以抛出错误或设置错误状态
             throw new Error('提交评估响应无效，缺少 submission_id。');
        }

        commit('SET_LOADING', false);
        return response; // 返回响应，可能包含 submission_id
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '提交评估失败。';
        console.error('[Action: submitAssessment] 失败。', error.response || error);
        commit('SET_ERROR', errorMessage);
        commit('SET_LOADING', false);
        throw error; // 重新抛出错误，让 UI 处理
      }
    },

    // --- 心理小贴士 actions ---
    async fetchRandomTip({ commit }) {
      // 获取随机心理小贴士
      console.log('[Action: fetchRandomTip] 触发。');
      try {
        const response = await api.encyclopedia.getRandomTip(); // 调用 API
        console.log('[Action: fetchRandomTip] API 响应:', response);
        // 检查响应结构并获取第一个条目
        if (response && response.data && Array.isArray(response.data.entries) && response.data.entries.length > 0) {
          commit('SET_CURRENT_TIP', response.data.entries[0]); // 保存小贴士
        } else {
           // 如果没有获取到，可以设置一个默认的
           console.warn('[Action: fetchRandomTip] 响应中未找到小贴士条目。');
           commit('SET_CURRENT_TIP', { category: '提示', title: '小贴士', content: '保持积极心态，迎接每一天！' });
        }
        return response;
      } catch (error) {
        // 获取失败
        console.error('[Action: fetchRandomTip] 失败。', error.response || error);
        // 设置一个错误提示或默认值
        commit('SET_CURRENT_TIP', { category: '提示', title: '网络错误', content: '无法获取心理小贴士，请检查网络连接。' });
        return null; // 返回 null 表示失败
      }
    },

    // --- 报告 actions ---
     // +++ 新增: 获取报告状态的 Action +++
     async fetchReportStatus({ commit, state }) {
      const submissionId = state.assessment.submissionId;
      // 只在有 submissionId 时执行
      if (!submissionId) {
        console.warn('[Action: fetchReportStatus] 没有 submissionId，无法获取状态。');
        commit('SET_REPORT_STATUS', 'not_found'); // 或其他表示无效的状态
        return null;
      }

      console.log(`[Action: fetchReportStatus] 触发，检查 ID: ${submissionId} 的状态...`);
      // 注意：状态检查通常不设置全局 loading，因为它是后台轮询的一部分
      // commit('SET_LOADING', true); // 如果需要，可以启用
      commit('CLEAR_ERROR'); // 清除旧错误

      try {
        console.log('[Action: fetchReport] 使用的 api 实例默认 baseURL:', api.defaults.baseURL); // <--- 添加这行
        console.log(`[Action: fetchReport] 准备调用 api.reports.getReport，ID: ${submissionId}`); // <--- 添加这行
        const response = await api.reports.getReportStatus(submissionId);
        console.log('[Action: fetchReportStatus] API 响应:', response);
        if (response && response.data && response.data.status) {
          commit('SET_REPORT_STATUS', response.data.status); // 使用从 API 获取的状态更新 state
          return response.data.status; // 返回状态值
        } else {
          console.warn('[Action: fetchReportStatus] 无效的状态 API 响应结构。');
          commit('SET_REPORT_STATUS', 'failed'); // 响应无效视为失败
          return 'failed';
        }
      } catch (error) {
        console.error(`[Action: fetchReportStatus] 获取 ID: ${submissionId} 状态时出错。`, error.response || error);
        let statusToSet = 'failed';
        let errorMessage = "无法获取报告状态。";

        if (error.response?.status === 404) {
          console.log(`[Action: fetchReportStatus] 评估 ID: ${submissionId} 未找到 (404)。`);
          statusToSet = 'not_found'; // 使用特定状态表示未找到
          errorMessage = "评估记录未找到。";
        } else {
           errorMessage = error.response?.data?.detail || error.message || errorMessage;
        }
        commit('SET_REPORT_STATUS', statusToSet);
        // 状态检查失败通常不设置全局错误，避免干扰用户，但可以记录
        // commit('SET_ERROR', errorMessage);
        // commit('SET_LOADING', false); // 如果启用了 loading
        return statusToSet; // 返回最终确定的状态
      }
    },
    // ++++++++++++++++++++++++++++++++++++++++
    // VVVVVV 这里是替换后的 fetchReport action VVVVVV
    async fetchReport({ commit, state }) {
      const submissionId = state.assessment.submissionId;
      console.log(`[Action: fetchReport] 触发获取完整报告，ID: ${submissionId}。`);

      if (!submissionId) {
        console.warn('[Action: fetchReport] state 中没有可用的 submission ID。');
        commit('SET_REPORT', null); // 确保 report 为空
        return null;
      }

      commit('CLEAR_ERROR');
      // 获取完整报告时可以显示加载状态
      commit('SET_LOADING', true);

      try {
        console.log(`[Action: fetchReport] 正在调用 API 获取完整报告，ID: ${submissionId}...`);
        const response = await api.reports.getReport(submissionId);
        console.log('[Action: fetchReport] 收到 API 响应:', response);

        // 后端现在应该只在报告完成时返回 report 数据
        if (response && response.data && response.data.report) {
            commit('SET_REPORT', response.data.report); // 保存有效的报告数据
            console.log(`[Action: fetchReport] 已接收并保存完整报告数据，ID: ${submissionId}。`);
            // 如果 API 在报告未完成时仍返回 200 和 message，这里可以处理
        } else if (response && response.data && response.data.message) {
             console.warn(`[Action: fetchReport] API 返回了消息而非报告: ${response.data.message}. 报告可能未就绪或失败。`);
             commit('SET_REPORT', null); // 确保报告为空
             // 可以根据 message 更新状态或错误
             if (response.data.message.includes("失败")) {
                  commit('SET_REPORT_STATUS', 'failed');
                  commit('SET_ERROR', response.data.message);
             }
        }
         else {
            console.warn('[Action: fetchReport] 无效的 API 响应结构或未包含报告数据。');
            commit('SET_REPORT', null);
            commit('SET_ERROR', '获取报告时响应无效。'); // 设置错误
        }
        commit('SET_LOADING', false);
        return response; // 返回原始响应

      } catch (error) {
        // 处理 API 调用错误
        let errorMessage = "无法获取分析报告。";
        if (error.response) {
          console.error(`[Action: fetchReport] 服务器响应错误状态: ${error.response.status}`, error.response.data);
          errorMessage = error.response.data?.detail || errorMessage;
          if (error.response.status === 404) {
             errorMessage = "评估记录未找到。"; // 更具体的 404 消息
             commit('SET_REPORT_STATUS', 'not_found'); // 更新状态
          } else if (error.response.status === 401 || error.response.status === 403) {
             errorMessage = "身份验证失败或无权限。";
          }
        } else if (error.request) {
          console.error(`[Action: fetchReport] 未收到服务器响应。`);
          errorMessage = "服务器未响应，请检查网络连接。";
        } else {
          console.error(`[Action: fetchReport] 设置请求时出错:`, error.message);
          errorMessage = `请求出错: ${error.message}`;
        }
        console.error(`[Action: fetchReport] 获取 ID: ${submissionId} 的报告失败。`, error);
        commit('SET_ERROR', errorMessage); // 设置全局错误
        commit('SET_REPORT', null); // 清空报告
        commit('SET_LOADING', false);
        throw error; // 重新抛出，让调用者知道失败
      }
    },
    // ^^^^^^ 这里是替换后的 fetchReport action ^^^^^^

    // --- 重置 actions ---
    resetAssessment({ commit }) {
      // 重置评估相关状态 (调用 mutation)
       console.log('[Action: resetAssessment] 触发。');
      commit('RESET_ASSESSMENT');
    },

    clearError({ commit }) {
      // 清除错误状态 (调用 mutation)
      commit('CLEAR_ERROR');
    }
  }
});

export default store;