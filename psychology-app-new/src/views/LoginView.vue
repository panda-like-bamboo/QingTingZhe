<!-- 文件路径: psychology-app-new/src/views/LoginView.vue (最终版) -->
<template>
  <div class="page-container login-page">
    <div class="tech-circles">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="floating-icons">
        <i class="fas fa-brain icon icon-1"></i>
        <i class="fas fa-project-diagram icon icon-2"></i> <!-- 使用 project-diagram 替代 -->
        <i class="fas fa-microscope icon icon-3"></i>
        <i class="fas fa-dna icon icon-4"></i>
      </div>
    </div>
    
    <div class="logo-container">
      <!-- [->] 关键修改: 将图标替换为图片 -->
      <img src="@/assets/police_emblem.png" alt="警徽" class="emblem-image" />
      <h1>“倾听者”AI智能警务分析评估应用系统<span class="tech-badge">AI</span></h1>
    </div>

    <div class="card login-card">
      <div class="card-header">
        <i class="fas fa-user-circle"></i>
        <h2>用户登录</h2>
      </div>

      <form @submit.prevent="handleLoginSubmit">
        <div class="form-group">
          <label for="username">
            <i class="fas fa-user form-icon"></i>
            用户名 (身份证号/手机号)
          </label>
          <input
            type="text"
            id="username"
            v-model="username"
            required
            placeholder="请输入用户名"
          />
        </div>

        <div class="form-group">
          <label for="password">
            <i class="fas fa-lock form-icon"></i>
            密码
          </label>
          <div class="password-input-container">
            <input
              :type="showPassword ? 'text' : 'password'"
              id="password"
              v-model="password"
              required
              placeholder="请输入密码"
            />
            <button 
              type="button" 
              class="toggle-password" 
              @click="showPassword = !showPassword"
              title="切换密码可见性"
            >
              <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
        </div>

        <div v-if="error" class="error-message">
          <i class="fas fa-exclamation-circle"></i>
          {{ error }}
        </div>

        <button type="submit" class="btn btn-block" :disabled="loading">
          <i class="fas fa-sign-in-alt btn-icon"></i>
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <div class="register-link">
        还没有账号？
        <router-link to="/register">
          <i class="fas fa-user-plus"></i> 立即注册
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
// Script 部分无需修改
import { mapState, mapActions } from 'vuex';

export default {
  name: 'LoginView',
  data() {
    return {
      username: '',
      password: '',
      loading: false,
      error: '',
      showPassword: false
    };
  },
  computed: {
    ...mapState({
      storeError: state => state.error
    })
  },
  watch: {
    storeError(newError) {
      this.error = newError;
    }
  },
  methods: {
    ...mapActions(['login', 'clearError']),
    async handleLoginSubmit() {
      console.log('Login button clicked, executing LoginView handleLoginSubmit method...');
      this.error = '';
      this.loading = true;
      try {
        await this.login({
          username: this.username,
          password: this.password
        });
        console.log('LoginView: Vuex action call presumably successful (no error thrown).');
        this.$router.push('/user-info');
      } catch (error) {
        console.error('LoginView: Caught error after Vuex action call:', error);
      } finally {
        this.loading = false;
      }
    }
  },
  created() {
    this.clearError();
    this.error = '';
  }
}
</script>

<style scoped>
/* 原有样式保持不变 */
.login-page {
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  min-height: 100vh; padding: 20px; position: relative; overflow: hidden;
}
.tech-circles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; }
.circle { position: absolute; border-radius: 50%; opacity: 0.05; background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); }
.circle-1 { width: 500px; height: 500px; top: -100px; right: -100px; }
.circle-2 { width: 300px; height: 300px; bottom: -50px; left: -50px; }
.floating-icons { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.icon { position: absolute; color: var(--primary-color); opacity: 0.1; filter: drop-shadow(0 0 5px var(--primary-color)); }
.icon-1 { top: 15%; left: 10%; font-size: 40px; animation: float 4s ease-in-out infinite; }
.icon-2 { top: 30%; right: 15%; font-size: 30px; animation: float 5s ease-in-out infinite 1s; }
.icon-3 { bottom: 20%; left: 20%; font-size: 36px; animation: float 6s ease-in-out infinite 0.5s; }
.icon-4 { bottom: 30%; right: 10%; font-size: 42px; animation: float 7s ease-in-out infinite 1.5s; }

.logo-container {
  text-align: center;
  margin-bottom: 40px;
  animation: float 3s ease-in-out infinite;
}

/* [->] 关键修改: 替换 logo-icon 为 emblem-image 的样式 */
.emblem-image {
  width: 90px;
  height: auto;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 10px rgba(33, 150, 243, 0.5));
}

h1 {
  font-size: 28px; color: var(--primary-color); font-family: var(--heading-font);
  letter-spacing: 2px; position: relative;
}
.tech-badge {
  font-size: 14px; background: var(--accent-color); color: white; padding: 2px 6px;
  border-radius: 4px; position: relative; top: -10px; margin-left: 5px; font-family: var(--heading-font);
}
.login-card {
  width: 100%; max-width: 400px; padding: 30px; background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px); border: 1px solid rgba(33, 150, 243, 0.2);
}
.card-header { display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
.card-header i { font-size: 28px; color: var(--primary-color); margin-right: 12px; }
h2 { margin: 0; color: var(--primary-dark); font-size: 22px; }
.form-group { margin-bottom: 20px; }
label { display: flex; align-items: center; margin-bottom: 8px; font-weight: 500; color: var(--text-secondary); }
.form-icon { margin-right: 8px; color: var(--primary-color); }
.password-input-container { position: relative; }
.toggle-password {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 0; font-size: 16px;
}
.toggle-password:hover { color: var(--primary-color); }
.btn-icon { margin-right: 8px; }
.error-message {
  display: flex; align-items: center; background-color: rgba(255, 82, 82, 0.1);
  border-left: 4px solid var(--error-color); padding: 12px; margin-bottom: 20px;
  border-radius: var(--border-radius);
}
.error-message i { color: var(--error-color); margin-right: 10px; font-size: 16px; }
.register-link { margin-top: 25px; text-align: center; font-size: 14px; color: var(--text-secondary); }
.register-link a {
  color: var(--primary-color); text-decoration: none; font-weight: 600;
  display: inline-flex; align-items: center; margin-left: 5px;
}
.register-link a i { margin-right: 5px; }
.register-link a:hover { color: var(--primary-dark); text-decoration: underline; }
.fa-project-diagram:before { content: "\f542"; } /* 备用图标 */
</style>