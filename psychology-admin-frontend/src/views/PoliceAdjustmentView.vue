<!-- 文件路径: psychology-admin-frontend/src/views/PoliceAdjustmentView.vue -->
<template>
  <div class="guidance-container">
    <div class="page-header">
      <h2><i class="fas fa-shield-alt"></i> 民辅警心理调适</h2>
      <p>输入民辅警信息以查询评估报告，并获取专业的心理调适建议。</p>
    </div>
    <GuidanceForm scenario="police" />
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