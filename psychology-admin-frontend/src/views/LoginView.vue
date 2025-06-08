<!-- 文件路径: psychology-admin-frontend/src/views/LoginView.vue (添加渐变背景版) -->
<template>
  <div class="login-container">
    <div class="login-box">
      <img src="@/assets/police_emblem.png" alt="警徽" class="emblem-image" />

      <h1 class="system-title">
        “倾听者”
        <span class="subtitle">AI智能警务分析评估应用系统</span>
      </h1>
      
      <p class="login-prompt">请使用您的凭据登录</p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <i class="fas fa-user"></i>
            <input
              type="text"
              id="username"
              v-model="username"
              required
              placeholder="请输入用户名"
            />
          </div>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <i class="fas fa-lock"></i>
            <input
              type="password"
              id="password"
              v-model="password"
              required
              placeholder="请输入密码"
            />
          </div>
        </div>
        <div v-if="error" class="alert alert-danger">
          {{ error }}
        </div>
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          <span v-if="loading"><i class="fas fa-spinner fa-spin"></i> 登录中...</span>
          <span v-else>登 录</span>
        </button>
      </form>
    </div>
    <footer class="login-footer">
      技术支持：倾听者项目组
    </footer>
  </div>
</template>

<script setup>
// Script 部分无需修改
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const store = useStore();
const router = useRouter();

const loading = computed(() => store.state.loading);
const error = computed(() => store.state.error);

const handleLogin = async () => {
  store.commit('CLEAR_ERROR');
  try {
    await store.dispatch('login', {
      username: username.value,
      password: password.value,
    });
  } catch (err) {
    console.error("Login failed:", err);
  }
};
</script>

<style scoped>
/* [->] 关键修改: 为 .login-container 添加渐变背景 */
.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100%;
  
  /* 直接从全局变量引用或在此处硬编码渐变色 */
  /* 方案一：引用全局变量 (推荐，保持一致) */
  background-color: var(--background-gradient-start, #d4e6f1);
  background-image: linear-gradient(135deg, var(--background-gradient-start, #d4e6f1) 0%, var(--background-gradient-end, #85c1e9) 100%);
  
  /* 方案二：在此处硬编码 (如果想让登录页背景与众不同) */
  /* background-color: #d4e6f1; */
  /* background-image: linear-gradient(135deg, #d4e6f1 0%, #85c1e9 100%); */
}

/* 其他样式保持不变 */
.login-box {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.emblem-image {
  width: 90px;
  height: auto;
  margin-bottom: 20px;
}

.system-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0 0 10px;
  line-height: 1.2;
}

.system-title .subtitle {
  display: block;
  font-size: 16px;
  font-weight: 400;
  color: #555;
  margin-top: 8px;
}

.login-prompt {
  color: #6c757d;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-wrapper {
  position: relative;
}

.input-wrapper i {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #adb5bd;
}

.input-wrapper input {
  width: 100%;
  padding: 12px 12px 12px 40px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 16px;
  box-sizing: border-box;
}

.alert-danger {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 20px;
}

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
}

.login-footer {
  margin-top: 40px;
  font-size: 14px;
  color: #888;
}
</style>