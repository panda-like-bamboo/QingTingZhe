<!-- 已经废弃 -->

<template>
  <div class="guidance-container">
    <header class="page-header">
      <h1><i class="fas fa-route"></i> 专项指导方案生成</h1>
      <p>根据人员的历史评估报告，由AI生成针对性的指导方案。</p>
    </header>

    <!-- 输入表单 -->
    <div class="card input-card">
      <form @submit.prevent="handleGenerate" class="guidance-form">
        <div class="form-group">
          <label for="scenario">选择方案类型</label>
          <select id="scenario" v-model="scenario" required>
            <option disabled value="">请选择...</option>
            <option value="petitioner">上访户情绪疏导方案</option>
            <option value="juvenile">未成年人心理辅导方案</option>
            <option value="police">民辅警心理调适建议</option>
          </select>
        </div>
        <div class="form-group">
          <label for="idCard">人员身份证号</label>
          <input 
            type="text" 
            id="idCard" 
            v-model="idCard" 
            required
            placeholder="请输入要查询的人员身份证号"
          />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <i class="fas fa-cogs"></i>
          {{ loading ? '正在生成...' : '生成方案' }}
        </button>
      </form>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container card">
      <div class="loading-indicator">
        <i class="fas fa-spinner fa-spin"></i>
        <span>AI 正在分析并生成方案，请稍候...</span>
      </div>
      <loading-tip :tip="staticTip" />
    </div>

    <!-- 错误信息展示 -->
    <div v-if="localError && !loading" class="error-display card">
      <div class="error-content">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ localError }}</span>
      </div>
      <button @click="handleGenerate" class="btn btn-secondary btn-small">
        <i class="fas fa-sync-alt"></i> 重试
      </button>
    </div>

    <!-- 成功结果展示 -->
    <div v-if="currentGuidance && !loading" class="result-container">
      <div class="card result-card">
        <h3><i class="fas fa-file-alt"></i> 相关评估报告摘要</h3>
        <!-- 修改这里：从 pre 改为 div 并使用 v-html -->
        <div class="markdown-content" v-html="renderMarkdown(currentGuidance.report.report_text)"></div>
      </div>
      <div class="card result-card guidance-card">
        <h3><i class="fas fa-lightbulb"></i> AI 生成的指导方案</h3>
        <!-- 修改这里：从 pre 改为 div 并使用 v-html -->
        <div class="markdown-content" v-html="renderMarkdown(currentGuidance.guidance)"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import { marked } from 'marked'; // 引入 marked 库
import LoadingTip from '../components/LoadingTip.vue';

export default {
  name: 'GuidanceGeneratorView',
  components: {
    LoadingTip,
  },
  data() {
    return {
      scenario: '',
      idCard: '',
      localError: null,
      staticTip: {
        category: '操作提示',
        title: '耐心等待',
        content: 'AI模型正在进行深度分析，生成高质量的指导方案可能需要几十秒甚至更长时间，请您耐心等待，无需重复点击。'
      }
    };
  },
  computed: {
    ...mapState(['currentGuidance', 'loading']),
    globalError() {
      return this.$store.state.error;
    }
  },
  watch: {
    globalError(newError) {
      if (newError && !this.localError) {
        this.localError = newError;
      }
    }
  },
  methods: {
    ...mapActions(['fetchGuidance']),
    // 添加 renderMarkdown 方法
    renderMarkdown(text) {
      if (!text) return '';
      return marked(text);
    },
    async handleGenerate() {
      if (!this.scenario || !this.idCard.trim()) {
        this.localError = '请选择方案类型并输入身份证号。';
        return;
      }
      
      this.localError = null;
      this.$store.commit('CLEAR_ERROR');
      this.$store.commit('SET_CURRENT_GUIDANCE', null);

      try {
        await this.fetchGuidance({ 
          scenario: this.scenario, 
          idCard: this.idCard.trim() 
        });
      } catch (error) {
        this.localError = error.message || '生成方案时发生未知错误，请检查网络或联系管理员。';
      }
    },
  },
  created() {
    this.$store.commit('CLEAR_ERROR');
    this.$store.commit('SET_CURRENT_GUIDANCE', null);
  },
};
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; color: var(--primary-color); display: flex; align-items: center; }
.page-header h1 i { margin-right: 12px; }
.page-header p { color: #888; }
.input-card { margin-bottom: 24px; }
.guidance-form { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 16px; }
.guidance-form .form-group { flex: 1 1 250px; margin-bottom: 0; }
.guidance-form select, .guidance-form input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 4px; }
.loading-container { display: flex; flex-direction: column; align-items: center; }
.loading-indicator, .error-display { text-align: center; padding: 40px; color: #888; font-size: 16px; }
.loading-indicator i { margin-right: 8px; }
.error-display { display: flex; justify-content: space-between; align-items: center; background-color: #fff1f0; border: 1px solid #ffa39e; color: #f5222d; padding: 16px 24px; }
.error-content { display: flex; align-items: center; }
.error-content i { margin-right: 10px; font-size: 18px; }
.btn-small { padding: 6px 12px; font-size: 14px; }
.btn-secondary { background-color: #6c757d; }
.btn-secondary:hover { background-color: #5a6268; }
.result-container { margin-top: 24px; }
.result-card { margin-bottom: 24px; }
.result-card h3 { margin-top: 0; margin-bottom: 16px; color: var(--primary-color); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; display: flex; align-items: center; }
.result-card h3 i { margin-right: 10px; }
.guidance-card { border-left: 4px solid var(--accent-color); }
.guidance-card h3 { color: var(--accent-color); }

/* ++ 添加 Markdown 渲染样式 ++ */
.markdown-content {
  line-height: 1.7;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 4px;
}
:deep(.markdown-content h1), 
:deep(.markdown-content h2), 
:deep(.markdown-content h3) {
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  color: var(--secondary-color);
  font-weight: 600;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
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
:deep(.markdown-content li) {
    margin-bottom: 0.5em;
}
</style>