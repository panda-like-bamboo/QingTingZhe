<template>
  <div class="report-detail-container">
    <header class="page-header">
      <h1><i class="fas fa-file-invoice"></i> 评估报告详情</h1>
      <p v-if="report">报告 ID: {{ report.id }} | 被测者: {{ report.subject_name }}</p>
    </header>

    <div v-if="loading" class="loading-indicator">
      <i class="fas fa-spinner fa-spin"></i>
      <span>正在加载报告...</span>
    </div>

    <div v-else-if="error" class="error-display">
      <i class="fas fa-exclamation-triangle"></i>
      <span>{{ error }}</span>
    </div>

    <div v-else-if="report" class="report-layout">
      <!-- 左侧：基础信息 -->
      <div class="card info-panel">
        <h3><i class="fas fa-user-circle"></i> 基础信息</h3>
        <ul>
          <li><strong>姓名:</strong> {{ report.subject_name }}</li>
          <li><strong>年龄:</strong> {{ report.age }}</li>
          <li><strong>性别:</strong> {{ report.gender }}</li>
          <li><strong>身份证号:</strong> {{ report.id_card || '未提供' }}</li>
          <li><strong>职业:</strong> {{ report.occupation || '未提供' }}</li>
          <li><strong>案件名称:</strong> {{ report.case_name || '未提供' }}</li>
          <li><strong>量表类型:</strong> {{ report.questionnaire_type || '仅图片分析' }}</li>
          <li><strong>提交时间:</strong> {{ new Date(report.created_at).toLocaleString('zh-CN') }}</li>
        </ul>
      </div>

      <!-- 右侧：报告正文和标签 -->
      <div class="main-panel">
        <div class="card report-content-card">
          <h3><i class="fas fa-brain"></i> AI 综合分析报告</h3>
          <div class="markdown-content" v-html="renderMarkdown(report.report_text)"></div>
        </div>
        
        <div class="card tags-card">
          <h3><i class="fas fa-tags"></i> 关联属性标签</h3>
          <div v-if="report.attributes && report.attributes.length > 0" class="tags-container">
            <span v-for="attr in report.attributes" :key="attr.id" class="tag">
              {{ attr.name }}
            </span>
          </div>
          <p v-else class="no-tags">暂无关联标签。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import { marked } from 'marked';

export default {
  name: 'ReportDetailView',
  props: {
    id: {
      type: [String, Number],
      required: true,
    },
  },
  computed: {
    ...mapState({
      report: state => state.currentReport,
      loading: state => state.loading,
      error: state => state.error,
    }),
  },
  methods: {
    ...mapActions(['fetchReportById']),
    renderMarkdown(text) {
      if (!text) return '<p>报告内容为空。</p>';
      return marked(text);
    },
  },
  created() {
    this.fetchReportById(this.id);
  },
  beforeRouteUpdate(to, from, next) {
    this.fetchReportById(to.params.id);
    next();
  },
};
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; color: var(--primary-color); display: flex; align-items: center; }
.page-header h1 i { margin-right: 12px; }
.page-header p { color: #888; }
.loading-indicator, .error-display { text-align: center; padding: 60px 20px; }
.loading-indicator i, .error-display i { display: block; font-size: 40px; margin-bottom: 16px; }
.report-layout { display: grid; grid-template-columns: 300px 1fr; gap: 24px; }
@media (max-width: 992px) { .report-layout { grid-template-columns: 1fr; } }
.card h3 { margin-top: 0; margin-bottom: 16px; color: var(--primary-color); display: flex; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
.card h3 i { margin-right: 10px; }
.info-panel ul { list-style: none; padding: 0; }
.info-panel li { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.info-panel li:last-child { border-bottom: none; }
.info-panel strong { color: var(--secondary-color); margin-right: 8px; }
.markdown-content { line-height: 1.7; }
/* 使用 :deep() 选择器来确保样式能应用到 v-html 生成的内容上 */
:deep(.markdown-content h1), 
:deep(.markdown-content h2), 
:deep(.markdown-content h3),
:deep(.markdown-content h4),
:deep(.markdown-content h5),
:deep(.markdown-content h6) {
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  color: var(--secondary-color);
  font-weight: 600;
}
:deep(.markdown-content p) {
    margin-bottom: 1em;
}
:deep(.markdown-content ul),
:deep(.markdown-content ol) {
    padding-left: 2em;
    margin-bottom: 1em;
}
:deep(.markdown-content strong) {
    color: var(--primary-color);
}
.tags-container { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { background-color: #e6f7ff; border: 1px solid #91d5ff; color: #1890ff; padding: 4px 10px; border-radius: 4px; font-size: 14px; }
.no-tags { color: #888; }
</style>
/* 该组件用于显示评估报告的详细信息,包括基础信息、AI综合分析报告和关联属性标签 */