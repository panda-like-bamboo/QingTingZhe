<template>
  <div class="assessment-search-container">
    <header class="page-header">
      <h1><i class="fas fa-search"></i> 评估查询</h1>
      <p>通过身份证号查询历史评估记录，或查看所有最新记录。</p>
    </header>

    <!-- 搜索区域 -->
    <div class="card search-card">
      <form @submit.prevent="handleSearch" class="search-form">
        <div class="form-group">
          <label for="idCardSearch">身份证号 (可选)</label>
          <input 
            type="text" 
            id="idCardSearch" 
            v-model="searchIdCard" 
            placeholder="输入身份证号进行精确查询"
          />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <i class="fas fa-search"></i>
          {{ loading ? '查询中...' : '查 询' }}
        </button>
      </form>
    </div>

    <!-- 结果展示区域 -->
    <div class="card result-card">
      <div v-if="loading" class="loading-indicator">
        <i class="fas fa-spinner fa-spin"></i>
        <span>正在加载数据...</span>
      </div>
      <div v-else-if="error" class="error-display">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
      </div>
      <div v-else-if="!searched && assessments.length === 0" class="empty-state">
        <i class="fas fa-info-circle"></i>
        <p>默认显示最新评估记录。您也可以输入身份证号进行精确查询。</p>
      </div>
      <div v-else-if="assessments.length === 0" class="empty-state">
        <i class="fas fa-file-excel"></i>
        <p>未找到与查询条件匹配的评估记录。</p>
      </div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>评估ID</th>
              <th>被测者姓名</th>
              <th>量表类型</th>
              <th>评估状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="assessment in assessments" :key="assessment.id">
              <td>{{ assessment.id }}</td>
              <td>{{ assessment.subject_name }}</td>
              <td>{{ assessment.questionnaire_type || '仅图片' }}</td>
              <td>
                <span :class="['status-tag', getStatusClass(assessment.status)]">
                  {{ formatStatus(assessment.status) }}
                </span>
              </td>
              <td>{{ new Date(assessment.created_at).toLocaleString('zh-CN') }}</td>
              <td>
                <button class="btn btn-small" @click="viewReport(assessment.id)">
                  查看报告
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'AssessmentSearchView',
  data() {
    return {
      searchIdCard: '',
      searched: false, // 标记是否已执行过搜索
    };
  },
  computed: {
    ...mapState(['assessments', 'loading', 'error']),
  },
  methods: {
    ...mapActions(['searchAssessments']),
    handleSearch() {
      this.searched = true;
      this.searchAssessments(this.searchIdCard.trim() || null);
    },
    viewReport(assessmentId) {
      this.$router.push({ name: 'ReportDetail', params: { id: assessmentId } });
    },
    formatStatus(status) {
      const statusMap = {
        pending: '待处理',
        processing: '处理中',
        complete: '已完成',
        failed: '失败',
      };
      return statusMap[status] || status;
    },
    getStatusClass(status) {
      return `status-${status}`;
    }
  },
  created() {
    this.$store.commit('CLEAR_ERROR');
    // 初始加载所有评估记录
    this.searchAssessments(null);
  }
};
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; color: var(--primary-color); display: flex; align-items: center; }
.page-header h1 i { margin-right: 12px; }
.page-header p { color: #888; }
.search-card { margin-bottom: 24px; }
.search-form { display: flex; align-items: flex-end; gap: 16px; }
.search-form .form-group { flex-grow: 1; margin-bottom: 0; }
.result-card .loading-indicator,
.result-card .error-display,
.result-card .empty-state { text-align: center; padding: 40px; color: #888; font-size: 16px; }
.result-card .loading-indicator i,
.result-card .error-display i,
.result-card .empty-state i { display: block; font-size: 32px; margin-bottom: 16px; }
.table-wrapper { overflow-x: auto; }
.status-tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; color: white; }
.status-pending { background-color: #909399; }
.status-processing { background-color: #409eff; }
.status-complete { background-color: var(--accent-color); }
.status-failed { background-color: #f56c6c; }
.btn-small { padding: 4px 8px; font-size: 12px; }
</style>