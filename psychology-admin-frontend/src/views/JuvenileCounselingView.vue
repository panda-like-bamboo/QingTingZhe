<!-- 文件路径: psychology-admin-frontend/src/views/JuvenileCounselingView.vue -->
<template>
  <div class="guidance-container">
    <div class="page-header">
      <h2><i class="fas fa-child"></i> 未成年人心理辅导</h2>
      <p>输入未成年人信息以查询评估报告，并生成定制化的心理辅导方案。</p>
    </div>
    <GuidanceForm scenario="juvenile" />
  </div>
</template>

<script setup>
import GuidanceForm from '@/components/GuidanceForm.vue';
</script>

<style scoped>
/* 样式与 PetitionerGuidanceView 相同 */
.guidance-container {
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
</style>