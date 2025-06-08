<!-- 文件路径: psychology-admin-frontend/src/views/DashboardView.vue (功能增强版) -->
<template>
  <div class="dashboard-container">
    <!-- 1. 页面标题 -->
    <div class="page-header">
      <!-- [->] 修改标题 -->
      <h2><i class="fas fa-chart-pie"></i> 数据分析</h2>
      <p>查看系统关键指标，并获取AI智能分析洞察。</p>
    </div>

    <!-- 加载与错误提示 -->
    <div v-if="isLoading" class="loading-state">
      <LoadingTip message="正在加载统计数据..." />
    </div>
    <div v-if="error" class="error-state alert alert-danger">
      加载数据时出错: {{ error }}
    </div>

    <div v-if="stats && !isLoading" class="content-wrapper">
      <!-- 2. 数据图表网格布局 -->
      <div class="dashboard-grid">
        <div class="chart-card card">
          <h3>用户年龄分布</h3>
          <div class="chart-wrapper">
            <Pie v-if="stats.ageData" :data="getChartJsData(stats.ageData, '年龄分布')" :options="chartOptions" />
          </div>
        </div>
        <div class="chart-card card">
          <h3>用户性别分布</h3>
          <div class="chart-wrapper">
            <Doughnut v-if="stats.genderData" :data="getChartJsData(stats.genderData, '性别分布')" :options="chartOptions" />
          </div>
        </div>
      </div>

      <!-- 3. [+] AI 智能分析区 -->
      <div class="ai-analysis-section card">
        <div class="ai-header">
          <h3><i class="fas fa-robot"></i> AI 智能分析</h3>
          <button @click="runAIAnalysis" class="btn btn-primary" :disabled="aiLoading">
            <span v-if="aiLoading"><i class="fas fa-spinner fa-spin"></i> 分析中...</span>
            <span v-else><i class="fas fa-play-circle"></i> 启动 AI 分析</span>
          </button>
        </div>
        <div class="ai-content">
          <div v-if="aiLoading" class="loading-tip-small">
            <LoadingTip message="AI 正在深度解读数据，请稍候..." />
          </div>
          <div v-else-if="aiError" class="alert alert-danger">
            AI 分析失败: {{ aiError }}
          </div>
          <div v-else-if="aiAnalysisResult" class="markdown-content" v-html="renderMarkdown(aiAnalysisResult)">
          </div>
          <div v-else class="placeholder">
            点击“启动 AI 分析”按钮，获取关于当前数据的智能洞察和建议。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useStore } from 'vuex';
import { Pie, Doughnut } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale, LinearScale } from 'chart.js';
import LoadingTip from '@/components/LoadingTip.vue';
import api from '@/api'; // [+] 导入 api
import { marked } from 'marked'; // [+] 导入 marked 用于渲染 Markdown

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale);

const store = useStore();

const isLoading = computed(() => store.state.loading);
const error = computed(() => store.state.error);
const stats = computed(() => store.state.stats);

// [+] AI 分析相关状态
const aiLoading = ref(false);
const aiError = ref(null);
const aiAnalysisResult = ref('');

// --- AI 分析方法 ---
const runAIAnalysis = async () => {
  if (!stats.value) return;
  aiLoading.value = true;
  aiError.value = null;
  aiAnalysisResult.value = '';
  try {
    const response = await api.stats.getAIAnalysis(stats.value);
    aiAnalysisResult.value = response.data.analysis_text;
  } catch (err) {
    aiError.value = err.response?.data?.detail || err.message || '未知错误';
  } finally {
    aiLoading.value = false;
  }
};

// --- Markdown 渲染 ---
const renderMarkdown = (text) => {
  return marked(text);
};


// Chart.js 辅助函数
const getChartJsData = (chartData, label) => {
  if (!chartData || !chartData.labels || !chartData.values) return { labels: [], datasets: [] };
  return {
    labels: chartData.labels,
    datasets: [{
      label: label,
      backgroundColor: ['#42A5F5', '#66BB6A', '#FFA726', '#26A69A', '#AB47BC', '#FF7043', '#8D6E63', '#EC407A', '#78909C'],
      data: chartData.values
    }]
  };
};

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' }, title: { display: false } }
};

onMounted(() => {
  store.dispatch('fetchStats');
});
</script>

<style scoped>
.dashboard-container { width: 100%; height: 100%; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 12px; }
.page-header p { color: #6c757d; margin-top: 4px; }

.loading-state, .error-state { text-align: center; padding: 40px; }

/* [+] 新增: 内容区总包裹器 */
.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); 
  gap: 24px; 
}
.chart-card {
  background-color: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
}
.chart-card h3 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.chart-wrapper { position: relative; height: 350px; }

/* [+] 新增: AI 分析区样式 */
.ai-analysis-section {
  padding: 24px;
}
.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 16px;
  margin-bottom: 20px;
}
.ai-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.ai-content {
  min-height: 150px; /* 防止内容变化时跳动 */
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.placeholder {
  text-align: center;
  color: #6c757d;
  font-style: italic;
}
.markdown-content {
  line-height: 1.7;
}
/* 深度选择器，用于设置 v-html 内容的样式 */
:deep(.markdown-content ul) {
  padding-left: 20px;
  margin-top: 1em;
}
:deep(.markdown-content li) {
  margin-bottom: 0.5em;
}

@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
}

.alert-danger { color: #991b1b; background-color: #fee2e2; border-color: #fecaca; padding: 15px; border-radius: 6px; }
</style>