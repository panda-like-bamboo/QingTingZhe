<!-- 文件路径: psychology-admin-frontend/src/views/PetitionerGuidanceView.vue -->
<template>
  <div class="guidance-container">
    <!-- 页面头部，提供标题和描述 -->
    <div class="page-header">
      <h2>
        <!-- 使用 Font Awesome 图标增强视觉效果 -->
        <i class="fas fa-hand-holding-heart"></i> 
        上访户情绪疏导
      </h2>
      <p>输入上访户信息以查询评估报告，并生成针对性的情绪疏导方案。</p>
    </div>

    <!-- 
      引用核心的表单组件 GuidanceForm.vue
      通过 'scenario' prop 传递当前场景为 'petitioner'（上访户）
      这使得 GuidanceForm 组件可以被复用在不同场景下
    -->
    <GuidanceForm scenario="petitioner" />
  </div>
</template>

<script setup>
// 使用 Vue 3 的 <script setup> 语法，这是当前推荐的最佳实践
// 它使得代码更简洁，并且组件会自动注册
import GuidanceForm from '@/components/GuidanceForm.vue';
// 此处无需编写 export default 或 components 注册，Vue 会自动处理
</script>

<style scoped>
/* 'scoped' 属性确保这些样式只作用于当前组件，不会污染全局样式 */
.guidance-container {
  /* 为整个容器提供内边距，使其内容不会紧贴边缘 */
  padding: 24px;
  background-color: #f8f9fa; /* 添加一个柔和的背景色 */
  min-height: calc(100vh - 56px); /* 确保内容区域至少占满视口高度 */
}

.page-header {
  /* 头部和下方表单之间的间距 */
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #dee2e6; /* 添加一条分割线，使结构更清晰 */
}

.page-header h2 {
  font-size: 24px;
  font-weight: 700;
  /* 使用 flex 布局让图标和文字对齐 */
  display: flex;
  align-items: center;
  /* 图标和文字之间的间距 */
  gap: 12px;
  color: #343a40; /* 使用更深的颜色以突出标题 */
}

.page-header p {
  /* 描述文字使用更柔和的颜色 */
  color: #6c757d;
  margin-top: 4px;
}
</style>