<!-- 文件路径: psychology-admin-frontend/src/views/LawQueryView.vue -->
<template>
  <div class="law-query-container">
    <div class="page-header">
      <h2><i class="fas fa-balance-scale"></i> 法律法规查询</h2>
      <p>快速查找常用法律法规，并链接至国家官方数据库。</p>
    </div>

    <div class="search-bar card">
      <i class="fas fa-search search-icon"></i>
      <input
        type="text"
        v-model="searchQuery"
        placeholder="输入法规名称进行筛选..."
        class="search-input"
      />
    </div>

    <div class="law-list">
      <div v-for="law in filteredLaws" :key="law.id" class="law-item card">
        <div class="law-info">
          <h3 class="law-name">{{ law.name }}</h3>
          <p class="law-description">{{ law.description }}</p>
        </div>
        <div class="law-actions">
          <a :href="law.link" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
            <i class="fas fa-external-link-alt"></i> 查看原文
          </a>
        </div>
      </div>
       <div v-if="filteredLaws.length === 0" class="no-results card">
        <p>未找到匹配的法规。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { laws } from '@/data/laws.js';

const searchQuery = ref('');

const filteredLaws = computed(() => {
  if (!searchQuery.value) {
    return laws;
  }
  return laws.filter(law =>
    law.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});
</script>

<style scoped>
.law-query-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header p {
  color: #6c757d;
  margin-top: 4px;
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding: 8px 16px;
}

.search-icon {
  color: #9ca3af;
  margin-right: 12px;
}

.search-input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 16px;
}

.law-list {
  display: grid;
  gap: 16px;
}

.law-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  transition: box-shadow 0.3s, transform 0.3s;
}

.law-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.law-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--primary-color);
}

.law-description {
  font-size: 14px;
  color: #4b5563;
  margin: 0;
}

.no-results {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}
</style>