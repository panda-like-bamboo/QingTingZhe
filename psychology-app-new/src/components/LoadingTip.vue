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
    <div class="tip-decoration">
      <div class="tip-dots">
        <div class="tip-dot"></div>
        <div class="tip-dot"></div>
        <div class="tip-dot"></div>
      </div>
    </div>
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
        title: '今日小贴士',
        content: '保持正念与关注当下可以有效减轻压力和焦虑。'
      })
    }
  }
}
</script>

<style scoped>
.loading-tip {
  background: linear-gradient(135deg, var(--card-bg), rgba(255, 255, 255, 0.9));
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
  margin: 20px auto;
  max-width: 90%;
  position: relative;
  border-left: 4px solid var(--secondary-color);
  transform: perspective(1000px) rotateX(0deg);
  transition: transform 0.5s;
}

.loading-tip:hover {
  transform: perspective(1000px) rotateX(2deg);
  box-shadow: var(--glow-effect);
}

.tip-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.tip-icon {
  font-size: 24px;
  color: var(--secondary-color);
  margin-right: 16px;
  animation: pulse 2s infinite;
}

.tip-title-group {
  flex: 1;
}

.tip-category {
  color: var(--secondary-color);
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.tip-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
  font-family: var(--heading-font);
}

.tip-content {
  line-height: 1.6;
  font-size: 16px;
  color: var(--text-secondary);
  padding-left: 40px;
}

.tip-decoration {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.tip-dots {
  display: flex;
  gap: 4px;
}

.tip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--secondary-color);
  opacity: 0.5;
}

.tip-dot:nth-child(1) {
  animation: pulse 2s infinite;
}

.tip-dot:nth-child(2) {
  animation: pulse 2s infinite 0.3s;
}

.tip-dot:nth-child(3) {
  animation: pulse 2s infinite 0.6s;
}
</style>