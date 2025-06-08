<template>
  <div class="list-container">
    <div class="list-header">
      <h2>审讯记录列表</h2>
      <p>查看、搜索和管理所有已保存的审讯记录。</p>
    </div>

    <!-- 加载与错误提示 -->
    <div v-if="isLoading" class="loading-state">
      <LoadingTip message="正在加载记录列表..." />
    </div>
    <div v-if="error" class="error-state alert alert-danger">
      加载列表时出错: {{ error }}
    </div>

    <!-- 记录表格 -->
    <div v-if="!isLoading && !error" class="card">
      <table class="record-table">
        <thead>
          <tr>
            <th>记录ID</th>
            <th>被讯问人</th>
            <th>案件类型</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>最后更新</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="records.length === 0">
            <td colspan="7" class="text-center">没有找到任何审讯记录。</td>
          </tr>
          <tr v-for="record in records" :key="record.id">
            <td>{{ record.id }}</td>
            <td>{{ record.person_name || '未命名' }}</td>
            <td>{{ record.case_type || '未分类' }}</td>
            <td><span :class="['status-badge', getStatusClass(record.status)]">{{ record.status }}</span></td>
            <td>{{ formatDateTime(record.created_at) }}</td>
            <td>{{ formatDateTime(record.updated_at) }}</td>
            <td>
              <button @click="editRecord(record.id)" class="btn btn-primary btn-small">
                <i class="fas fa-edit"></i> 编辑
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页控件 -->
    <div v-if="!isLoading && total > 0" class="pagination">
      <button @click="prevPage" :disabled="currentPage === 1">上一页</button>
      <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页 (总计 {{ total }} 条)</span>
      <button @click="nextPage" :disabled="currentPage === totalPages">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import LoadingTip from '@/components/LoadingTip.vue';

const store = useStore();
const router = useRouter();

const currentPage = ref(1);
const limit = ref(10);

const isLoading = computed(() => store.state.loading);
const error = computed(() => store.state.error);
const records = computed(() => store.state.interrogationList.records);
const total = computed(() => store.state.interrogationList.total);

const totalPages = computed(() => Math.ceil(total.value / limit.value) || 1);

const fetchRecords = () => {
  const skip = (currentPage.value - 1) * limit.value;
  store.dispatch('fetchInterrogationList', { skip, limit: limit.value });
};

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A';
  return new Date(dateTimeString).toLocaleString('zh-CN');
};

const getStatusClass = (status) => {
  if (status === 'completed') return 'status-completed';
  if (status === 'ongoing') return 'status-ongoing';
  return 'status-default';
};

const editRecord = (id) => {
  router.push({ name: 'InterrogationEdit', params: { id } });
};

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchRecords();
  }
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    fetchRecords();
  }
};

onMounted(() => {
  fetchRecords();
});
</script>

<style scoped>
.list-container {
  padding: 24px;
}

.list-header {
  margin-bottom: 24px;
}

.list-header h2 {
  font-size: 24px;
  font-weight: 700;
}

.list-header p {
  color: #6c757d;
}

.card {
  background-color: #fff;
  border-radius: 8px;
  padding: 0; /* 表格自带边距 */
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden; /* 让圆角对表格生效 */
}

.record-table {
  width: 100%;
  border-collapse: collapse;
}

.record-table th, .record-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
}

.record-table th {
  background-color: #fafafa;
  font-weight: 600;
}

.record-table tbody tr:hover {
  background-color: #f5f5f5;
}

.text-center {
  text-align: center;
  padding: 40px;
  color: #888;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.status-completed {
  background-color: #28a745; /* 绿色 */
}

.status-ongoing {
  background-color: #ffc107; /* 黄色 */
  color: #333;
}

.status-default {
  background-color: #6c757d; /* 灰色 */
}

.btn-small {
  padding: 4px 10px;
  font-size: 13px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
}

.pagination button {
  padding: 8px 16px;
}
</style>