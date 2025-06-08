<template>
  <div class="nav-bar">
    <div class="nav-left" @click="goBack" v-if="canGoBack">
      <div class="back-button">
        <i class="fas fa-chevron-left"></i>
      </div>
    </div>
    <div class="nav-title">
      <i class="fas fa-brain nav-icon"></i>
      <span>{{ title }}</span>
    </div>
    <div class="nav-right">
      <div class="status-indicator">
        <span class="pulse-dot"></span>
        <span class="status-text">AI</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NavBar',
  props: {
    title: {
      type: String,
      required: true
    },
    canGoBack: {
      type: Boolean,
      default: true
    }
  },
  methods: {
    goBack() {
      if (this.canGoBack) {
        this.$router.back();
      }
    }
  }
}
</script>

<style scoped>
.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  background: linear-gradient(90deg, var(--primary-dark), var(--primary-color));
  color: white;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 0 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.nav-left {
  display: flex;
  align-items: center;
  width: 60px;
}

.back-button {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color var(--transition-speed);
}

.back-button:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.nav-title {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  font-size: 20px;
  font-weight: 500;
  font-family: var(--heading-font);
  letter-spacing: 1px;
}

.nav-icon {
  margin-right: 10px;
  color: var(--secondary-light);
  font-size: 22px;
  animation: glow 2s infinite;
}

.nav-right {
  display: flex;
  justify-content: flex-end;
  width: 60px;
}

.status-indicator {
  display: flex;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 4px 8px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: var(--secondary-color);
  border-radius: 50%;
  margin-right: 6px;
  animation: pulse 2s infinite;
}

.status-text {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
}
</style>