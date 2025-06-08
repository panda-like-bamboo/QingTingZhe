<template>
  <aside class="sidebar" :style="{ width: '250px' }">
    <div class="sidebar-header">
      <i class="fas fa-brain logo-icon"></i>
      <h1>倾听者后台</h1>
    </div>
    <nav class="sidebar-nav">
      <ul>
        <li>
          <router-link to="/" exact-active-class="active">
            <i class="fas fa-chart-pie"></i>
            <span>数据分析</span>
          </router-link>
        </li>
        <li>
          <router-link to="/assessment-search" active-class="active">
            <i class="fas fa-search"></i>
            <span>评估查询</span>
          </router-link>
        </li>
        <li>
          <router-link to="/user-management" active-class="active">
            <i class="fas fa-users"></i>
            <span>用户管理</span>
          </router-link>
        </li>
        <li>
          <router-link to="/petitioner-guidance" active-class="active">
            <i class="fas fa-hand-holding-heart"></i>
            <span>上访户情绪疏导</span>
          </router-link>
        </li>
        <li>
          <router-link to="/juvenile-counseling" active-class="active">
            <i class="fas fa-child"></i>
            <span>未成年人心理辅导</span>
          </router-link>
        </li>
        <li>
          <router-link to="/police-adjustment" active-class="active">
            <i class="fas fa-shield-alt"></i>
            <span>民辅警心理调适</span>
          </router-link>
        </li>
        <li>
          <router-link to="/law-query" active-class="active">
            <i class="fas fa-balance-scale"></i>
            <span>法规查询</span>
          </router-link>
        </li>
        <li class="nav-item-dropdown" :class="{ 'open': isInterrogationOpen }">
          <a @click.prevent="toggleInterrogationMenu">
            <i class="fas fa-gavel"></i>
            <span>智能审讯</span>
            <i class="fas fa-chevron-down dropdown-arrow"></i>
          </a>
          <ul v-show="isInterrogationOpen" class="submenu">
            <li>
              <router-link to="/interrogation/new" active-class="active">
                <i class="fas fa-plus-circle"></i>
                <span>新建审讯</span>
              </router-link>
            </li>
            <li>
              <router-link to="/interrogation/list" active-class="active">
                <i class="fas fa-list-alt"></i>
                <span>查看记录</span>
              </router-link>
            </li>
          </ul>
        </li>
      </ul>
    </nav>
    <div class="sidebar-footer">
      <button @click="logout" class="logout-btn">
        <i class="fas fa-sign-out-alt"></i>
        <span>退出登录</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter, useRoute } from 'vue-router';

const store = useStore();
const router = useRouter();
const route = useRoute();
const isInterrogationOpen = ref(false);

const toggleInterrogationMenu = () => {
  isInterrogationOpen.value = !isInterrogationOpen.value;
};

watch(route, (newRoute) => {
  if (newRoute.path.startsWith('/interrogation')) {
    isInterrogationOpen.value = true;
  }
}, { immediate: true });

const logout = () => {
  store.dispatch('logout');
};
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
  transition: width 0.3s;
}

.sidebar-header {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid var(--secondary-color);
}
.logo-icon {
  font-size: 2em;
  margin-bottom: 10px;
}
.sidebar-header h1 {
  margin: 0;
  font-size: 1.5em;
}
.sidebar-nav {
  flex-grow: 1;
  overflow-y: auto;
}
.sidebar-nav ul {
  list-style: none;
  padding: 0;
  margin: 20px 0;
}
.sidebar-nav li a {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  color: var(--sidebar-text);
  text-decoration: none;
  transition: background-color 0.3s;
}
.sidebar-nav li a:hover, .sidebar-nav li a.active {
  background-color: var(--sidebar-active-bg);
  color: white;
}
.sidebar-nav li a i {
  margin-right: 15px;
  width: 20px;
  text-align: center;
}
.sidebar-footer {
  padding: 20px;
  border-top: 1px solid var(--secondary-color);
}
.logout-btn {
  width: 100%;
  padding: 10px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logout-btn:hover {
  background-color: #c0392b;
}
.logout-btn i {
  margin-right: 8px;
}
.nav-item-dropdown > a {
  cursor: pointer;
  position: relative;
}
.dropdown-arrow {
  margin-left: auto;
  transition: transform 0.3s ease;
}
.nav-item-dropdown.open > a .dropdown-arrow {
  transform: rotate(180deg);
}
.submenu {
  list-style: none;
  padding: 0;
  background-color: var(--secondary-color);
  margin: 0;
}
.submenu li a {
  padding-left: 40px;
}
.submenu li a i {
  font-size: 0.8em;
}
</style>