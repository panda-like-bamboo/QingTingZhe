<template>
  <div class="loading-tip">
    <div class="tip-header">
      <i class="fas fa-lightbulb tip-icon"></i>
      <div class="tip-title-group">
        <div class="tip-category">{{ tip.category }}</div>
        <div class="tip-title">{{ tip.title }}</div>
      </div>
    </div>
    <div class="tip-content">{{ tip.content }}</div>
  </div>
</template>

<script>
export default {
  name: 'LoadingTip',
  props: {
    tip: {
      type: Object,
      required: true,
      default: () => ({
        category: '心理小贴士',
        title: '每日提示',
        content: '保持积极的心态有助于应对挑战。'
      })
    }
  }
}
</script>

<style scoped>
.loading-tip {
  background-color: #e6f7ff;
  border-left: 4px solid #1890ff;
  border-radius: 4px;
  padding: 16px;
  margin: 24px auto;
  max-width: 600px;
}
.tip-header { display: flex; align-items: center; margin-bottom: 12px; }
.tip-icon { font-size: 20px; color: #1890ff; margin-right: 12px; }
.tip-title-group { flex: 1; }
.tip-category { color: #1890ff; font-size: 12px; font-weight: 600; text-transform: uppercase; }
.tip-title { font-size: 16px; font-weight: 600; color: var(--primary-color); }
.tip-content { line-height: 1.6; font-size: 14px; color: var(--text-color); }
</style>