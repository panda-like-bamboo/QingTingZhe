<template>
  <div class="page-container report-page">
    <nav-bar title="心理分析报告" :canGoBack="false" />

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>正在加载报告内容...</p>
    </div>

    <div v-else-if="!report && !loading" class="error-container card">
      <div class="error-icon-container">
        <i class="fas fa-file-excel error-icon"></i>
      </div>
      <h2>未能加载报告</h2>
      <p>报告可能仍在生成中，或加载失败。请稍后尝试刷新。</p>
      <div class="action-buttons">
        <button @click="checkReport" class="btn btn-secondary btn-small" :disabled="loading">
          <i class="fas fa-sync-alt"></i> {{ loading ? '刷新中...' : '手动刷新' }}
        </button>
        <button @click="startNew" class="btn btn-small">
          <i class="fas fa-redo"></i> 开始新测评
        </button>
      </div>
    </div>

    <div v-else class="report-container">
      <div class="report-header card">
        <div class="report-title">
          <i class="fas fa-brain header-icon"></i>
          <h2>{{ report.subject_name || '未知对象' }} 的心理分析报告</h2>
        </div>
        <div class="report-meta">
          <div class="meta-item">
            <i class="fas fa-calendar-alt meta-icon"></i>
            <span>生成时间: {{ formatDate(report.created_at) }}</span>
          </div>
          <div class="meta-item" v-if="report.questionnaire_type">
            <i class="fas fa-clipboard-list meta-icon"></i>
            <span>量表类型: {{ report.questionnaire_type }}</span>
          </div>
        </div>
      </div>

      <div class="report-body card">
        <div class="report-content markdown-content" v-html="$marked(report.report_text || '')"></div>
      </div>

      <div class="report-actions card">
        <button @click="startNew" class="btn btn-block">
          <i class="fas fa-plus-circle"></i> 开始新测评
        </button>
        
        <div class="action-buttons">
          <button class="btn btn-secondary btn-small">
            <i class="fas fa-print"></i> 打印报告
          </button>
          <button class="btn btn-secondary btn-small">
            <i class="fas fa-download"></i> 下载PDF
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions, mapGetters } from 'vuex';
import NavBar from '../components/NavBar.vue';
import { formatDate } from '../utils';

export default {
  name: 'ReportView',
  components: {
    NavBar
  },
  data() {
    return {
      loading: false
    };
  },
  computed: {
    ...mapState({
      report: state => state.report
    }),
    ...mapGetters(['getSubmissionId']),

    submissionId() {
      return this.getSubmissionId;
    }
  },
  methods: {
    ...mapActions(['fetchReport', 'resetAssessment']),

    formatDate,

    async checkReport() {
      if (!this.submissionId) {
        console.warn('ReportView: No submission ID found, cannot fetch report.');
        return;
      }

      console.log('ReportView: checkReport called, setting loading true.');
      this.loading = true;

      try {
        await this.fetchReport();
        console.log('ReportView: fetchReport action completed.');
      } catch (error) {
        console.error('ReportView: Error caught during checkReport -> fetchReport:', error);
      } finally {
        this.loading = false;
        console.log('ReportView: checkReport finished, setting loading false.');
      }
    },

    startNew() {
      console.log('ReportView: Starting new assessment.');
      this.resetAssessment();
      this.$router.push('/user-info');
    }
  },
  async created() {
    console.log('ReportView: Component created.');
    if (!this.report && this.submissionId) {
      console.log('ReportView: Report not found in store, and submissionId exists. Triggering initial fetch.');
      await this.checkReport();
    } else if (this.report) {
        console.log('ReportView: Report found in store on creation.');
    } else {
        console.log('ReportView: No report and no submissionId on creation.');
    }
  }
}
</script>

<style scoped>
.report-page {
  padding-top: 70px;
  padding-bottom: 40px;
  background-color: var(--background-color);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(33, 150, 243, 0.1);
  border-top: 4px solid var(--primary-color);
  border-radius: 50%;
  animation: rotate 1s linear infinite;
  margin-bottom: 20px;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  text-align: center;
  margin: 20px auto;
  max-width: 500px;
}

.error-icon-container {
  width: 80px;
  height: 80px;
  background-color: rgba(255, 82, 82, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.error-icon {
  font-size: 40px;
  color: var(--error-color);
}

.error-container h2 {
  margin-bottom: 16px;
  color: var(--primary-color);
  font-size: 22px;
}

.error-container p {
  margin-bottom: 24px;
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.report-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 16px;
}

.report-header {
  padding: 24px;
  margin-bottom: 20px;
  text-align: center;
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.05), rgba(63, 81, 181, 0.05));
  border-bottom: 2px solid rgba(33, 150, 243, 0.1);
}

.report-title {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.header-icon {
  font-size: 40px;
  color: var(--primary-color);
  margin-right: 16px;
  animation: glow 2s infinite;
}

.report-title h2 {
  font-size: 24px;
  color: var(--primary-color);
  margin: 0;
}

.report-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 14px;
}

.meta-icon {
  color: var(--secondary-color);
  margin-right: 8px;
}

.report-body {
  padding: 30px;
  margin-bottom: 20px;
}

.report-content {
  line-height: 1.8;
  color: var(--text-primary);
}

/* Markdown styles */
:deep(.markdown-content h1),
:deep(.markdown-content h2),
:deep(.markdown-content h3),
:deep(.markdown-content h4) {
  margin-top: 1.5em;
  margin-bottom: 0.8em;
  color: var(--primary-color);
  font-family: var(--heading-font);
}

:deep(.markdown-content h1) { font-size: 1.8em; }
:deep(.markdown-content h2) { font-size: 1.5em; }
:deep(.markdown-content h3) { font-size: 1.25em; }
:deep(.markdown-content h4) { font-size: 1.1em; }

:deep(.markdown-content p) {
  margin-bottom: 1em;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

:deep(.markdown-content li) {
  margin-bottom: 0.5em;
}

:deep(.markdown-content strong) {
  font-weight: bold;
  color: var(--primary-dark);
}

:deep(.markdown-content em) {
  font-style: italic;
}

:deep(.markdown-content blockquote) {
  border-left: 4px solid var(--secondary-color);
  padding-left: 16px;
  margin-left: 0;
  margin-right: 0;
  font-style: italic;
  color: var(--text-secondary);
}

.report-actions {
  padding: 24px;
  text-align: center;
}

.btn i {
  margin-right: 8px;
}
</style>