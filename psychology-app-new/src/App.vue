<template>
  <!-- [关键修复] 移除这个 div 上的 id="app" 属性 -->
  <div class="app-container"> 
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
// 这里不需要任何逻辑
</script>

<style>
/* 你可以在这里添加一些针对整个应用的容器样式，
   例如，确保它填满整个视口 */
.app-container {
  width: 100%;
  min-height: 100vh;
  position: relative; /* 用于页面过渡动画的定位 */
  overflow-x: hidden;
}

/* 页面切换过渡动画 */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>