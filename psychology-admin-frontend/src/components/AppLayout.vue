<!-- 文件路径: psychology-admin-frontend/src/components/AppLayout.vue (终极版) -->
<template>
  <div class="app-layout">
    <!-- 侧边栏组件 -->
    <SideBar />
    
    <!-- 主内容区域 -->
    <main class="main-content" :style="{ marginLeft: sidebarWidth + 'px' }">
      
      <!-- 路由视图 -->
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
      
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import SideBar from './SideBar.vue';

// 定义侧边栏宽度，确保与 SideBar.vue 的 CSS 宽度一致
const sidebarWidth = ref(250);
</script>

<style scoped>
.app-layout {
  display: flex;
  background-color: var(--background-color);
  min-height: 100vh;
  /* 关键: 防止父容器因为子元素宽度变化而影响整体布局 */
  overflow-x: hidden;
}

.main-content {
  /* [->] 关键修改: 使用 calc 和 vw 来定义一个绝对的、不收缩的宽度 */
  /* 100vw 是视口总宽度，减去侧边栏的宽度 */
  width: calc(100vw - 250px); 

  /* [-] 移除 flex-grow: 1; 因为我们现在使用精确的宽度计算，不再需要它来“填充”空间 */
  
  /* 其他样式保持不变，用于平滑过渡和内边距 */
  transition: margin-left 0.3s ease;
  padding: 0; /* [->] 移除通用内边距，让每个页面自己决定 */
  
  /* 如果内容超高，允许主内容区滚动 */
  overflow-y: auto; 
  height: 100vh; /* 确保 main-content 高度和视口一致，以便 overflow-y 生效 */
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>