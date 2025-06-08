<template>
  <div class="page-container register-page">
    <nav-bar title="注册账号" />

    <div class="card register-card">
      <div class="card-header">
        <i class="fas fa-user-plus"></i>
        <h2>创建新账号</h2>
      </div>

      <form @submit.prevent="handleRegisterSubmit">
        <div class="form-group">
          <label for="username">
            <i class="fas fa-user form-icon"></i>
            用户名
          </label>
          <input
            type="text"
            id="username"
            v-model="form.username"
            required
            placeholder="请输入用户名 (至少3个字符)"
            minlength="3"
            :class="{'input-valid': form.username.length >= 3 && form.username.length > 0}"
          />
          <div class="input-validation" v-if="form.username.length >= 3">
            <i class="fas fa-check-circle validation-icon"></i>
          </div>
        </div>

        <div class="form-group">
          <label for="email">
            <i class="fas fa-envelope form-icon"></i>
            邮箱
          </label>
          <input
            type="email"
            id="email"
            v-model="form.email"
            placeholder="请输入邮箱地址"
            :class="{'input-valid': isValidEmail}"
          />
          <div class="input-validation" v-if="isValidEmail">
            <i class="fas fa-check-circle validation-icon"></i>
          </div>
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
              v-model="form.password"
              required
              placeholder="请输入密码 (至少6个字符)"
              minlength="6"
              :class="{'input-valid': form.password.length >= 6 && form.password.length > 0}"
            />
            <button 
              type="button" 
              class="toggle-password" 
              @click="showPassword = !showPassword"
            >
              <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
          <div class="input-validation password-validation" v-if="form.password.length >= 6 && form.password.length > 0">
            <i class="fas fa-check-circle validation-icon"></i>
          </div>
        </div>

        <div class="form-group">
          <label for="confirmPassword">
            <i class="fas fa-shield-alt form-icon"></i>
            确认密码
          </label>
          <div class="password-input-container">
            <input
              :type="showPassword ? 'text' : 'password'"
              id="confirmPassword"
              v-model="confirmPassword"
              required
              placeholder="请再次输入密码"
              :class="{'input-valid': confirmPassword === form.password && confirmPassword.length > 0, 'input-invalid': passwordError}"
            />
            <div class="input-validation password-validation" v-if="confirmPassword === form.password && confirmPassword.length > 0">
              <i class="fas fa-check-circle validation-icon"></i>
            </div>
          </div>
          <div v-if="passwordError" class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            {{ passwordError }}
          </div>
        </div>

        <div v-if="error" class="error-message">
          <i class="fas fa-exclamation-triangle"></i>
          注册失败: {{ formatError(error) }}
        </div>

        <div v-if="registrationSuccess" class="success-message">
          <i class="fas fa-check-circle"></i>
          注册成功！请前往登录。
        </div>

        <button type="submit" class="btn btn-block" :disabled="loading || !!passwordError">
          <i class="fas fa-user-plus btn-icon"></i>
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <div class="login-link">
        已有账号？
        <router-link to="/login">
          <i class="fas fa-sign-in-alt"></i> 登录
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import NavBar from '../components/NavBar.vue';

export default {
  name: 'RegisterView',
  components: {
    NavBar
  },
  data() {
    return {
      form: {
        username: '',
        email: '',
        password: '',
        is_active: true
      },
      confirmPassword: '',
      loading: false,
      error: null,
      passwordError: '',
      registrationSuccess: false,
      showPassword: false
    };
  },
  computed: {
    isValidEmail() {
      if (!this.form.email) return false;
      const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      return re.test(String(this.form.email).toLowerCase());
    }
  },
  watch: {
    'form.password': function() {
      this.validatePasswordMatch();
    },
    confirmPassword: function() {
      this.validatePasswordMatch();
    }
  },
  methods: {
    validatePasswordMatch() {
      if (this.form.password && this.confirmPassword) {
        this.passwordError = this.form.password !== this.confirmPassword
          ? '两次输入的密码不一致'
          : '';
      } else {
        this.passwordError = '';
      }
    },
    
    formatError(err) {
      console.error("原始错误对象:", err);
      if (Array.isArray(err)) {
        return err.map(e => `${e.loc.join('.')}: ${e.msg}`).join('; ');
      }
      else if (typeof err === 'object' && err !== null && err.detail) {
         if (typeof err.detail === 'string') {
            return err.detail;
         } else if (Array.isArray(err.detail)) {
            return err.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join('; ');
         }
      }
      else if (typeof err === 'string') {
         return err;
      }
      else if (err && err.message) {
        return err.message;
      }
      return '发生未知错误，请检查控制台获取更多信息。';
    },
    
    async handleRegisterSubmit() {
      if (this.passwordError) return;

      this.error = null;
      this.registrationSuccess = false;
      this.loading = true;

      const payload = { ...this.form };

      if (!payload.email) {
        delete payload.email;
      }

      console.log('准备发送的注册数据:', payload);

      try {
        await this.$store.dispatch('register', payload);

        this.registrationSuccess = true;
        setTimeout(() => {
           this.$router.push('/login');
        }, 1500);

      } catch (err) {
        console.error('注册过程中捕获到错误:', err);
        this.error = err?.response?.data || err?.message || '注册失败，请检查输入或稍后再试。';

      } finally {
        this.loading = false;
      }
    }
  },
  created() {
    this.$store.dispatch('clearError');
  }
}
</script>

<style scoped>
.register-page {
  padding-top: 70px;
  padding-bottom: 40px;
  position: relative;
  overflow: hidden;
}

.register-card {
  margin: 20px auto;
  max-width: 500px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(33, 150, 243, 0.2);
  position: relative;
  z-index: 10;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.card-header i {
  font-size: 28px;
  color: var(--primary-color);
  margin-right: 12px;
}

h2 {
  margin: 0;
  color: var(--primary-dark);
  font-size: 22px;
  font-family: var(--heading-font);
}

.form-group {
  margin-bottom: 22px;
  position: relative;
}

label {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-icon {
  margin-right: 8px;
  color: var(--primary-color);
}

.password-input-container {
  position: relative;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  font-size: 16px;
  z-index: 1;
}

.toggle-password:hover {
  color: var(--primary-color);
}

.input-validation {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--success-color);
}

.password-validation {
  right: 40px;
}

.validation-icon {
  animation: fadeIn 0.3s;
}

.input-valid {
  border-color: var(--success-color) !important;
}

.input-invalid {
  border-color: var(--error-color) !important;
}

.error-message {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-top: 8px;
  margin-bottom: 16px;
  background-color: rgba(255, 82, 82, 0.1);
  border-left: 4px solid var(--error-color);
  color: var(--error-color);
  border-radius: var(--border-radius);
  font-size: 14px;
}

.error-message i {
  margin-right: 10px;
}

.success-message {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 16px;
  background-color: rgba(76, 175, 80, 0.1);
  border-left: 4px solid var(--success-color);
  color: var(--success-color);
  border-radius: var(--border-radius);
  font-weight: 500;
}

.success-message i {
  margin-right: 10px;
}

.btn-icon {
  margin-right: 8px;
}

.login-link {
  margin-top: 25px;
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
}

.login-link a {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  margin-left: 5px;
}

.login-link a i {
  margin-right: 5px;
}

.login-link a:hover {
  color: var(--primary-dark);
  text-decoration: underline;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>