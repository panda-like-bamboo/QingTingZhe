<template>
  <div class="interrogation-input-container wide-page-container">
    <header class="page-header">
      <h1><i class="fas fa-keyboard"></i> 智能审讯 - 信息录入</h1>
      <p>请填写审讯相关的基础信息以创建笔录。</p>
    </header>

    <div class="card wide-card">
      <form @submit.prevent="handleStart">
        <!-- 被讯问人信息 -->
        <h3 class="form-section-title">被讯问人信息</h3>
        <div class="form-row">
          <div class="form-group">
            <label for="name">姓名 <span class="required">*</span></label>
            <input type="text" id="name" v-model="form.person_name" required />
          </div>
          <div class="form-group">
            <label for="gender">性别 <span class="required">*</span></label>
            <select id="gender" v-model="form.person_gender" required>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="age">年龄 <span class="required">*</span></label>
            <input type="number" id="age" v-model.number="form.person_age" required min="0" />
          </div>
          <div class="form-group checkbox-group">
            <input type="checkbox" id="is_minor" v-model="form.is_minor" />
            <label for="is_minor">是否未成年</label>
          </div>
        </div>
        <div class="form-group">
          <label for="id_card">身份证号</label>
          <input type="text" id="id_card" v-model="form.person_id_type_number" />
        </div>
        <div class="form-group">
          <label for="address">家庭住址</label>
          <input type="text" id="address" v-model="form.person_address" />
        </div>
        <div class="form-group">
          <label for="contact">联系方式</label>
          <input type="text" id="contact" v-model="form.person_contact" />
        </div>

        <!-- 审讯信息 -->
        <h3 class="form-section-title">审讯信息</h3>
        <div class="form-group">
          <label for="location">审讯地点 <span class="required">*</span></label>
          <input type="text" id="location" v-model="form.interrogation_location" required />
        </div>
        <div class="form-row">
            <div class="form-group">
                <label for="interrogator_count">讯问人员数量</label>
                <input type="number" id="interrogator_count" v-model.number="form.interrogator_count" min="1" />
            </div>
            <div class="form-group">
                <label for="interrogator_ids">讯问人员警号</label>
                <input type="text" id="interrogator_ids" v-model="form.interrogator_ids" placeholder="多个警号用逗号分隔" />
            </div>
        </div>
        
        <div v-if="error" class="error-display">{{ error }}</div>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <i class="fas fa-play-circle"></i> {{ loading ? '正在创建...' : '创建笔录并开始' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
export default {
  name: 'InterrogationInputView',
  data() {
    return {
      form: {
        person_name: '',
        person_gender: '男',
        person_age: null,
        is_minor: false,
        person_id_type_number: '',
        person_address: '',
        person_contact: '',
        interrogation_location: '',
        interrogator_count: null,
        interrogator_ids: '',
      },
    };
  },
  computed: {
    ...mapState(['loading', 'error']),
  },
  watch: {
      'form.person_age'(newAge) {
          if (newAge && newAge < 18) {
              this.form.is_minor = true;
          }
      }
  },
  methods: {
    ...mapActions(['startInterrogation']),
    async handleStart() {
      if (!this.form.person_name || !this.form.person_gender || !this.form.person_age || !this.form.interrogation_location) {
        alert('请填写所有带 * 的必填项');
        return;
      }
      try {
        const record = await this.startInterrogation(this.form);
        this.$router.push({ name: 'InterrogationEdit', params: { id: record.id } });
      } catch (error) {
        // 错误已在 store 中处理并显示在页面上
      }
    },
  },
  created() {
    this.$store.commit('CLEAR_ERROR');
  },
};
</script>

<style scoped>
/* 为特定页面设置更宽的容器 */
.wide-page-container .wide-card {
    max-width: 900px; /* 您可以根据需要调整这个宽度 */
    margin-left: auto;
    margin-right: auto;
}

.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; color: var(--primary-color); display: flex; align-items: center; }
.page-header h1 i { margin-right: 12px; }
.page-header p { color: #888; }
.form-section-title {
    font-size: 18px;
    color: var(--primary-color);
    margin-top: 30px;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-color);
}
.form-row {
    display: flex;
    gap: 20px;
}
.form-row .form-group {
    flex: 1;
}
.checkbox-group {
    display: flex;
    align-items: center;
    padding-top: 20px;
}
.checkbox-group input {
    width: auto;
    margin-right: 10px;
}
.checkbox-group label {
    margin-bottom: 0;
    font-weight: normal;
}
.required {
    color: #f5222d;
    margin-left: 4px;
}
.error-display { color: #f5222d; margin-top: 10px; }
button i { margin-right: 8px; }
</style>