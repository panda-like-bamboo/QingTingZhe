<!-- 文件路径: psychology-admin-frontend/src/views/InterrogationEditView.vue (最终优化版) -->
<template>
  <div class="editor-page-container">
    <!-- 1. 页面头部 -->
    <div class="page-header">
      <h2>审讯笔录编辑</h2>
      <p v-if="basicInfo" class="subtitle">
        被讯问人: {{ basicInfo.person_name || '未知' }} | 记录ID: {{ recordId }}
      </p>
    </div>

    <!-- 加载与错误提示 -->
    <div v-if="isLoading" class="loading-state">
      <LoadingTip message="正在加载审讯记录..." />
    </div>
    <div v-if="error" class="error-state alert alert-danger">
      加载记录时出错: {{ error }}
    </div>

    <!-- 2. 主编辑区 (左右布局) -->
    <div v-if="!isLoading && !error" class="editor-main-content">
      <!-- 左侧：问答记录列表 (可滚动) -->
      <div class="qa-list-panel">
        <div v-for="(qa, index) in qas" :key="qa.id || index" class="qa-pair">
          <div class="qa-header">
            <h4>第 {{ index + 1 }} 组问答</h4>
            <button @click="removeQaPair(index)" class="btn-remove" title="删除此问答对">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="qa-grid">
            <div class="form-group">
              <label :for="'question-' + index">问题</label>
              <textarea
                :id="'question-' + index"
                v-model="qa.q"
                class="form-control"
                rows="5"
                placeholder="请输入问题..."
              ></textarea>
            </div>
            <div class="form-group">
              <label :for="'answer-' + index">回答</label>
              <textarea
                :id="'answer-' + index"
                v-model="qa.a"
                class="form-control"
                rows="5"
                placeholder="请输入回答..."
              ></textarea>
            </div>
          </div>
        </div>
        <button @click="addQaPair" class="btn btn-add-qa">
          <i class="fas fa-plus"></i> 添加新问答
        </button>
      </div>

      <!-- 右侧：AI 建议与操作区 (固定) -->
      <aside class="sidebar-actions">
        <div class="action-card">
          <h3><i class="fas fa-lightbulb"></i> AI 智能建议</h3>
          <button @click="fetchSuggestions" :disabled="suggestionsLoading" class="btn btn-primary btn-block">
            <span v-if="suggestionsLoading"><i class="fas fa-spinner fa-spin"></i> 正在获取...</span>
            <span v-else><i class="fas fa-magic"></i> 获取AI建议问题</span>
          </button>
          
          <!-- [+] 关键修改: 建议内容容器，设置最小高度以防止抖动 -->
          <div class="suggestions-content-wrapper">
            <div v-if="suggestionsLoading" class="loading-tip-small">
              <LoadingTip message="AI思考中..." />
            </div>
            
            <div v-else-if="suggestionsError" class="alert alert-danger">
              {{ suggestionsError }}
            </div>

            <div v-else-if="suggestions.length > 0" class="suggestions-list">
              <p>点击建议以快速添加：</p>
              <button
                v-for="(suggestion, index) in suggestions"
                :key="index"
                @click="applySuggestion(suggestion)"
                class="suggestion-item"
              >
                {{ suggestion }}
              </button>
            </div>
            <!-- 如果没有建议且没有错误，这里会是空的，但父容器高度保持不变 -->
          </div>
        </div>
      </aside>
    </div>

    <!-- 3. 页面底部固定操作栏 -->
    <div class="page-footer">
      <button @click="saveInterrogation" class="btn btn-primary btn-lg" :disabled="isSaving">
        <span v-if="isSaving"><i class="fas fa-spinner fa-spin"></i> 正在保存...</span>
        <span v-else><i class="fas fa-save"></i> 保存笔录</span>
      </button>
    </div>

    <!-- 顶部通知弹窗 -->
    <transition name="toast-fade">
      <div v-if="showNotification" :class="['notification-toast', notificationType]">
        <i :class="notificationType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
        <span>{{ notificationMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
// Script部分与上一版完全相同，无需修改
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import LoadingTip from '@/components/LoadingTip.vue';

const store = useStore();
const route = useRoute();
const router = useRouter();

const qas = ref([]);
const basicInfo = ref(null);
const isLoading = ref(true);
const isSaving = ref(false);
const error = ref(null);
const suggestions = ref([]);
const suggestionsLoading = ref(false);
const suggestionsError = ref(null);
const showNotification = ref(false);
const notificationMessage = ref('');
const notificationType = ref('success');

const recordId = computed(() => route.params.id);

const triggerNotification = (message, type = 'success', duration = 3000) => {
  notificationMessage.value = message;
  notificationType.value = type;
  showNotification.value = true;
  setTimeout(() => { showNotification.value = false; }, duration);
};

const loadRecord = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    let record = store.state.interrogationRecord;
    if (!record || record.id != recordId.value) {
      record = await store.dispatch('fetchInterrogationRecordById', recordId.value);
    }
    if (record) {
      qas.value = JSON.parse(JSON.stringify(record.qas || []));
      basicInfo.value = JSON.parse(JSON.stringify(record.basic_info || {}));
    } else {
      throw new Error("未能加载到审讯记录数据。");
    }
  } catch (err) {
    error.value = err.message || '加载审讯记录失败。';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

const addQaPair = () => {
  qas.value.push({ q: '', a: '', id: Date.now() });
};

const removeQaPair = (index) => {
  qas.value.splice(index, 1);
};

const fetchSuggestions = async () => {
  suggestionsLoading.value = true;
  suggestionsError.value = null;
  suggestions.value = [];
  try {
    const result = await store.dispatch('suggestQuestion', {
      recordId: recordId.value,
      currentQAs: qas.value.filter(qa => qa.q.trim() !== '' || qa.a.trim() !== ''),
    });
    suggestions.value = result;
  } catch (err) {
    suggestionsError.value = err.message || '获取建议时发生未知错误。';
    console.error(err);
  } finally {
    suggestionsLoading.value = false;
  }
};

const applySuggestion = (suggestion) => {
  qas.value.push({ q: suggestion, a: '', id: Date.now() });
};

const saveInterrogation = async () => {
  isSaving.value = true;
  error.value = null;
  try {
    const updatePayload = {
      qas: qas.value,
      basic_info: basicInfo.value,
    };
    await store.dispatch('saveInterrogation', { 
        recordId: recordId.value, 
        updateData: updatePayload 
    });
    triggerNotification('审讯笔录已成功保存！', 'success', 2000);
    setTimeout(() => {
      router.push({ name: 'InterrogationList' });
    }, 2100);
  } catch (err) {
    const errorMessage = err.message || '保存失败，请检查网络或联系管理员。';
    triggerNotification(errorMessage, 'error', 4000);
    console.error(err);
  } finally {
    isSaving.value = false;
  }
};

onMounted(() => {
  loadRecord();
});
</script>

<style scoped>
/* 1. 页面主容器 */
.editor-page-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background-color: #f0f2f5;
}

.page-header {
  padding: 0 24px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color);
  background-color: #fff;
}
.page-header h2 { font-size: 22px; font-weight: 700; padding: 20px 0; margin: 0; }
.subtitle { margin-top: -15px; padding-bottom: 15px; color: #6c757d; font-size: 14px; }

/* 加载和错误状态 */
.loading-state, .error-state {
  flex-grow: 1; display: flex; justify-content: center; align-items: center;
}

/* 2. 主编辑区 */
.editor-main-content {
  flex-grow: 1;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  padding: 24px;
  overflow: hidden;
}

/* 左侧问答列表面板 */
.qa-list-panel {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  overflow-y: auto;
}

/* 问答对卡片 */
.qa-pair {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  background-color: #f9fafb;
}
.qa-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}
.qa-header h4 { margin: 0; font-size: 16px; font-weight: 600; }
.btn-remove { background: none; border: none; color: #9ca3af; cursor: pointer; font-size: 16px; }
.btn-remove:hover { color: #ef4444; }

/* [->] 关键修改: 问答对内部网格布局，确保无重叠 */
.qa-grid {
  display: grid;
  grid-template-columns: 1fr 1fr; /* 两列等宽 */
  gap: 16px; /* 列间距 */
}
.form-group { margin: 0; } /* 移除 form-group 的外边距 */
.form-group label { font-weight: 500; margin-bottom: 8px; display: block; }
.form-control { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; resize: vertical; box-sizing: border-box; } /* 添加 box-sizing */
.form-control:focus { border-color: var(--accent-color); box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.2); outline: none; }
.btn-add-qa { width: 100%; padding: 12px; margin-top: 10px; border: 1px dashed var(--accent-color); background-color: #f0fdf4; color: var(--accent-color); font-weight: 600; }
.btn-add-qa:hover { background-color: #dcfce7; }

/* 右侧 AI 操作区 */
.sidebar-actions { display: flex; flex-direction: column; gap: 24px; }
.action-card { background-color: #ffffff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.action-card h3 { font-size: 18px; margin: 0 0 16px; font-weight: 600; }
.btn-block { width: 100%; }

/* [->] 关键修改: 建议内容容器，设置最小高度防止抖动 */
.suggestions-content-wrapper {
  margin-top: 16px;
  min-height: 150px; /* 设置一个最小高度 */
  display: flex;
  flex-direction: column;
}

.loading-tip-small {
  margin: auto; /* 在容器中居中 */
}
.suggestions-list {
  display: flex; flex-direction: column;
}
.suggestions-list p { font-size: 14px; color: #6b7280; margin-bottom: 8px; }
.suggestion-item { width: 100%; text-align: left; padding: 10px; background-color: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px; cursor: pointer; margin-bottom: 8px; }
.suggestion-item:hover { background-color: #e5e7eb; }

/* 3. 页面底部固定操作栏 */
.page-footer {
  flex-shrink: 0;
  padding: 16px 24px;
  background-color: #fff;
  border-top: 1px solid var(--border-color);
  text-align: right;
  box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .editor-main-content { grid-template-columns: 1fr; }
  .qa-list-panel { height: auto; max-height: 60vh; }
  .sidebar-actions { overflow-y: auto; }
}
@media (max-width: 768px) {
  .qa-grid { grid-template-columns: 1fr; }
  .qa-header { position: relative; }
  .btn-remove { position: absolute; top: -8px; right: -8px; background-color: #fff; border-radius: 50%; width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; }
}

/* 其他样式保持不变 */
.notification-toast { position: fixed; top: 80px; left: 50%; transform: translateX(-50%); padding: 12px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); display: flex; align-items: center; gap: 10px; color: white; z-index: 1000; font-size: 16px; font-weight: 500; }
.notification-toast.success { background-color: var(--accent-color); }
.notification-toast.error { background-color: #f5222d; }
.notification-toast i { font-size: 20px; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.5s, transform 0.5s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translate(-50%, -20px); }
.alert { padding: 15px; border-radius: 6px; }
.alert-danger { color: #991b1b; background-color: #fee2e2; border-color: #fecaca; }
</style>