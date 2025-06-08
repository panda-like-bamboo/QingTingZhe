<!-- 文件路径: psychology-admin-frontend/src/components/GuidanceForm.vue -->
<template>
  <div>
    <!-- 输入表单部分，仅在没有结果时显示 -->
    <div v-if="!result" class="form-card card">
      <form @submit.prevent="generateGuidance">
        <div class="form-group">
          <label for="id_card">请输入查询对象的身份证号:</label>
          <input 
            id="id_card"
            v-model="idCard" 
            type="text" 
            placeholder="输入身份证号进行查询" 
            required 
          />
        </div>
        
        <!-- 错误信息显示区域 -->
        <div v-if="error" class="alert alert-danger">
          {{ error }}
        </div>
        
        <!-- 提交按钮，根据加载状态显示不同内容 -->
        <button type="submit" class="btn btn-primary" :disabled="isLoading">
          <span v-if="isLoading"><i class="fas fa-spinner fa-spin"></i> 查询中...</span>
          <span v-else><i class="fas fa-search"></i> 查询并生成方案</span>
        </button>
      </form>
    </div>

      <!-- 结果显示部分 -->
      <div v-if="result" class="result-container">
        <!-- 报告摘要卡片 -->
        <div class="report-section card">
          <h3><i class="fas fa-lightbulb"></i> 关联心理评估报告</h3>
          <div class="markdown-content" v-html="renderMarkdown(result.report.report_text || '报告无文本内容。')"></div>
        </div>

      <!-- AI 指导方案卡片 -->
      <div class="guidance-section card">
        <h3><i class="fas fa-lightbulb"></i> AI 指导方案</h3>
        <!-- 使用 v-html 渲染由 marked.js 解析后的 Markdown 内容 -->
        <div class="markdown-content" v-html="renderMarkdown(result.guidance)"></div>
      </div>

      <!-- 返回按钮 -->
      <button @click="resetForm" class="btn btn-secondary">
        <i class="fas fa-arrow-left"></i> 返回重新查询
      </button>
    </div>
  </div>
</template>

<script setup>
// --- 导入依赖 ---
import { ref, defineProps } from 'vue';
import { useStore } from 'vuex'; // 用于访问 Vuex store
import { marked } from 'marked';   // 用于将 Markdown 文本转换为 HTML

// --- 定义组件属性 (Props) ---
const props = defineProps({
  // 'scenario' prop 决定了要调用哪个后端场景的 API
  scenario: {
    type: String,
    required: true,
  },
});

// --- 组件内部状态定义 (State) ---
const store = useStore();
const idCard = ref('');      // 绑定的身份证号输入
const result = ref(null);    // 存储从后端获取的完整结果 { report, guidance }
const isLoading = ref(false);// 控制加载状态
const error = ref(null);     // 存储错误信息

// ---核心业务逻辑 (Methods) ---
const generateGuidance = async () => {
  // 1. 重置状态
  isLoading.value = true;
  error.value = null;
  result.value = null;

  try {
    // 2. 调用 Vuex action，并传递必要的参数
    // 这是与状态管理层交互的唯一入口
    const data = await store.dispatch('fetchGuidance', { 
      scenario: props.scenario, 
      idCard: idCard.value 
    });
    
    // 3. 对返回的数据进行健壮性检查，这是非常关键的一步
    if (data && data.report && data.guidance) {
      // 如果数据结构正确，将其赋值给组件的本地状态 `result`
      result.value = data;
    } else {
      // 如果后端返回的数据结构不符合预期，主动抛出一个明确的错误
      console.error("从后端获取的指导方案数据格式不正确:", data);
      throw new Error("获取的数据格式无效，请检查后端响应或联系管理员。");
    }

  } catch (err) {
    // 4. 捕获任何在 dispatch 或后续处理中发生的错误
    // 将错误信息展示给用户
    error.value = err.message || '获取指导方案时发生未知错误。';
  } finally {
    // 5. 无论成功或失败，都结束加载状态
    isLoading.value = false;
  }
};

// --- 辅助函数 (Helpers) ---

// 使用 marked.js 将 Markdown 字符串转换为 HTML
const renderMarkdown = (text) => {
  return text ? marked(text) : '';
};

// 重置表单，以便用户进行下一次查询
const resetForm = () => {
  idCard.value = '';
  result.value = null;
  error.value = null;
  isLoading.value = false; // 确保加载状态也被重置
};
</script>

<style scoped>
/* 卡片式表单样式 */
.form-card, .report-section, .guidance-section {
  padding: 24px;
  background-color: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.form-card {
  max-width: 600px;
  margin: 0 auto; /* 在没有结果时居中显示 */
}

/* 结果容器布局 */
.result-container {
  display: flex;
  flex-direction: column;
  gap: 24px; /* 卡片之间的垂直间距 */
}

/* 表单组样式 */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #495057;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 16px;
}

.form-group input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}

/* 统一的按钮样式 */
.btn {
  display: inline-block;
  font-weight: 400;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  border: 1px solid transparent;
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 4px;
  transition: all 0.2s ease-in-out;
}

.btn-primary {
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
}
.btn-primary:not(:disabled):hover {
  background-color: #0069d9;
  border-color: #0062cc;
}
.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-secondary {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
  align-self: flex-start; /* 让返回按钮靠左 */
}
.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
}


/* 卡片标题样式 */
h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #343a40;
}

/* 报告文本预格式化样式 */
pre {
  white-space: pre-wrap;      /* 自动换行 */
  word-wrap: break-word;      /* 单词内换行 */
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  max-height: 400px;
  overflow-y: auto;          /* 内容超长时显示滚动条 */
  font-family: 'Courier New', Courier, monospace;
}

/* Markdown 内容渲染样式 */
.markdown-content {
  line-height: 1.7;
}

/* 使用 :deep() 选择器来穿透 scoped 样式，设置 v-html 内部元素的样式 */
:deep(.markdown-content ul), 
:deep(.markdown-content ol) {
  padding-left: 20px;
  margin-top: 1em;
  margin-bottom: 1em;
}

:deep(.markdown-content li) {
  margin-bottom: 0.5em;
}

/* 错误提示框样式 */
.alert-danger {
  margin-top: 16px;
  color: #721c24;
  background-color: #f8d7da;
  border-color: #f5c6cb;
  padding: 10px 15px;
  border-radius: 4px;
}
</style>