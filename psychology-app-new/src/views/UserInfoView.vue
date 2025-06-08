<template>
  <div class="page-container user-info-page">
    <nav-bar title="基本信息" :canGoBack="false" />
    
    <div class="card info-card">
      <div class="card-header">
        <i class="fas fa-user-edit"></i>
        <h2>请填写基本信息</h2>
      </div>
      
      <form @submit.prevent="submitInfo">
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-id-card"></i>
            <span>个人基本信息</span>
          </div>
          
          <div class="form-group">
            <label for="name">
              <i class="fas fa-user form-icon"></i>
              姓名 <span class="required">*</span>
            </label>
            <input 
              type="text" 
              id="name"
              v-model="form.name"
              required
              placeholder="请输入姓名"
            />
          </div>
          
          <div class="form-row">
            <div class="form-group form-group-half">
              <label for="gender">
                <i class="fas fa-venus-mars form-icon"></i>
                性别 <span class="required">*</span>
              </label>
              <div class="select-wrapper">
                <select 
                  id="gender"
                  v-model="form.gender"
                  required
                >
                  <option value="">请选择性别</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                  <option value="其他">其他</option>
                </select>
                <div class="select-arrow">
                  <i class="fas fa-chevron-down"></i>
                </div>
              </div>
            </div>
            
            <div class="form-group form-group-half">
              <label for="age">
                <i class="fas fa-birthday-cake form-icon"></i>
                年龄 <span class="required">*</span>
              </label>
              <input 
                type="number" 
                id="age"
                v-model="form.age"
                required
                placeholder="请输入年龄"
                min="1"
                max="120"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label for="id_card">
              <i class="fas fa-id-badge form-icon"></i>
              身份证号
            </label>
            <input 
              type="text" 
              id="id_card"
              v-model="form.id_card"
              placeholder="请输入身份证号"
            />
            <div v-if="idCardError" class="error-message">
              <i class="fas fa-exclamation-circle"></i>
              {{ idCardError }}
            </div>
          </div>
        </div>
        
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-briefcase"></i>
            <span>职业与联系方式</span>
          </div>
          
          <div class="form-row">
            <div class="form-group form-group-half">
              <label for="occupation">
                <i class="fas fa-briefcase form-icon"></i>
                职业
              </label>
              <input 
                type="text" 
                id="occupation"
                v-model="form.occupation"
                placeholder="请输入职业"
              />
            </div>
            
            <div class="form-group form-group-half">
              <label for="phone_number">
                <i class="fas fa-phone form-icon"></i>
                手机号
              </label>
              <input 
                type="tel" 
                id="phone_number"
                v-model="form.phone_number"
                placeholder="请输入手机号"
              />
              <div v-if="phoneError" class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                {{ phoneError }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-home"></i>
            <span>婚姻与家庭</span>
          </div>
          
          <div class="form-row">
            <div class="form-group form-group-half">
              <label for="marital_status">
                <i class="fas fa-heart form-icon"></i>
                婚姻状况
              </label>
              <div class="select-wrapper">
                <select 
                  id="marital_status"
                  v-model="form.marital_status"
                >
                  <option value="">请选择</option>
                  <option value="未婚">未婚</option>
                  <option value="已婚">已婚</option>
                  <option value="离异">离异</option>
                  <option value="丧偶">丧偶</option>
                </select>
                <div class="select-arrow">
                  <i class="fas fa-chevron-down"></i>
                </div>
              </div>
            </div>
            
            <div class="form-group form-group-half">
              <label for="children_info">
                <i class="fas fa-child form-icon"></i>
                子女情况
              </label>
              <input 
                type="text" 
                id="children_info"
                v-model="form.children_info"
                placeholder="请描述子女情况"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label for="domicile">
              <i class="fas fa-map-marker-alt form-icon"></i>
              归属地
            </label>
            <input 
              type="text" 
              id="domicile"
              v-model="form.domicile"
              placeholder="请输入户籍所在地"
            />
          </div>
        </div>
        
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-heartbeat"></i>
            <span>健康与背景</span>
          </div>
          
          <div class="form-group">
            <label for="health_status">
              <i class="fas fa-notes-medical form-icon"></i>
              健康情况
            </label>
            <textarea 
              id="health_status"
              v-model="form.health_status"
              placeholder="请描述健康情况"
              rows="3"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="criminal_record">
              <i class="fas fa-gavel form-icon"></i>
              有无犯罪前科
            </label>
            <div class="radio-group">
              <label class="radio-label">
                <input type="radio" v-model="form.criminal_record" value="0">
                <span class="radio-text">无</span>
              </label>
              <label class="radio-label">
                <input type="radio" v-model="form.criminal_record" value="1">
                <span class="radio-text">有</span>
              </label>
            </div>
          </div>
        </div>
        
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-balance-scale"></i>
            <span>案件信息</span>
          </div>
          
          <div class="form-row">
            <div class="form-group form-group-half">
              <label for="case_name">
                <i class="fas fa-folder-open form-icon"></i>
                案件名称
              </label>
              <input 
                type="text" 
                id="case_name"
                v-model="form.case_name"
                placeholder="请输入案件名称"
              />
            </div>
            
            <div class="form-group form-group-half">
              <label for="case_type">
                <i class="fas fa-tags form-icon"></i>
                案件类型
              </label>
              <input 
                type="text" 
                id="case_type"
                v-model="form.case_type"
                placeholder="请输入案件类型"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group form-group-half">
              <label for="identity_type">
                <i class="fas fa-user-tag form-icon"></i>
                人员身份
              </label>
              <input 
                type="text" 
                id="identity_type"
                v-model="form.identity_type"
                placeholder="请输入人员身份"
              />
            </div>
            
            <div class="form-group form-group-half">
              <label for="person_type">
                <i class="fas fa-users form-icon"></i>
                人员类型
              </label>
              <input 
                type="text" 
                id="person_type"
                v-model="form.person_type"
                placeholder="请输入人员类型"
              />
            </div>
          </div>
        </div>
        
        <div v-if="error" class="error-message global-error">
          <i class="fas fa-exclamation-triangle"></i>
          {{ error }}
        </div>
        
        <button type="submit" class="btn btn-block" :disabled="loading">
          <i class="fas fa-arrow-right"></i>
          下一步
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import NavBar from '../components/NavBar.vue';
import { validateIdCard, validatePhone, validateAge } from '../utils';

export default {
  name: 'UserInfoView',
  components: {
    NavBar
  },
  data() {
    return {
      form: {
        name: '',
        gender: '',
        age: '',
        id_card: '',
        occupation: '',
        phone_number: '',
        marital_status: '',
        children_info: '',
        criminal_record: '0',
        health_status: '',
        domicile: '',
        case_name: '',
        case_type: '',
        identity_type: '',
        person_type: ''
      },
      idCardError: '',
      phoneError: '',
      error: '',
      loading: false
    };
  },
  computed: {
    ...mapState({
      basicInfo: state => state.assessment.basicInfo,
      storeError: state => state.error
    })
  },
  watch: {
    storeError(newError) {
      if (newError) {
        this.error = newError;
      }
    },
    'form.id_card'() {
      this.validateIdCard();
    },
    'form.phone_number'() {
      this.validatePhone();
    }
  },
  methods: {
    ...mapActions(['setBasicInfo', 'clearError']),
    
    validateIdCard() {
      if (!this.form.id_card) {
        this.idCardError = '';
        return true;
      }
      
      if (!validateIdCard(this.form.id_card)) {
        this.idCardError = '请输入有效的身份证号';
        return false;
      }
      
      this.idCardError = '';
      return true;
    },
    
    validatePhone() {
      if (!this.form.phone_number) {
        this.phoneError = '';
        return true;
      }
      
      if (!validatePhone(this.form.phone_number)) {
        this.phoneError = '请输入有效的手机号';
        return false;
      }
      
      this.phoneError = '';
      return true;
    },
    
    validateAge() {
      if (!validateAge(this.form.age)) {
        this.error = '请输入有效的年龄';
        return false;
      }
      return true;
    },
    
    submitInfo() {
      // Validate required fields
      if (!this.form.name || !this.form.gender || !this.form.age) {
        this.error = '请填写必填字段 (姓名、性别、年龄)';
        return;
      }
      
      // Validate special fields
      if (!this.validateIdCard() || !this.validatePhone() || !this.validateAge()) {
        return;
      }
      
      this.error = '';
      
      // Convert criminal_record to number
      const formData = {
        ...this.form,
        criminal_record: parseInt(this.form.criminal_record, 10),
        age: parseInt(this.form.age, 10)
      };
      
      // Save to store
      this.setBasicInfo(formData);
      
      // Navigate to questionnaire
      this.$router.push('/questionnaire');
    }
  },
  created() {
    this.clearError();
    
    // Load from store if available
    if (this.basicInfo) {
      // Convert criminal_record back to string for select input
      this.form = {
        ...this.basicInfo,
        criminal_record: this.basicInfo.criminal_record.toString()
      };
    }
  }
}
</script>

<style scoped>
.user-info-page {
  padding-top: 70px;
  padding-bottom: 40px;
}

.info-card {
  margin: 20px auto;
  max-width: 800px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.95);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
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

.form-section {
  margin-bottom: 30px;
  border: 1px solid rgba(33, 150, 243, 0.1);
  border-radius: var(--border-radius);
  padding: 20px;
  background-color: rgba(248, 249, 250, 0.5);
  transition: box-shadow 0.3s ease;
}

.form-section:hover {
  box-shadow: 0 5px 15px rgba(33, 150, 243, 0.1);
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(33, 150, 243, 0.2);
  color: var(--primary-color);
  font-weight: 600;
  font-size: 18px;
  font-family: var(--heading-font);
}

.section-title i {
  margin-right: 10px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.form-group {
  margin-bottom: 20px;
  position: relative;
  flex: 1;
}

.form-group-half {
  flex: 0.5;
}

.form-icon {
  margin-right: 8px;
  color: var(--primary-color);
}

.required {
  color: var(--error-color);
  margin-left: 4px;
}

.select-wrapper {
  position: relative;
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--primary-color);
  pointer-events: none;
  transition: transform 0.3s;
}

select:focus + .select-arrow {
  transform: translateY(-50%) rotate(180deg);
}

.radio-group {
  display: flex;
  gap: 20px;
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.radio-label input {
  display: none;
}

.radio-text {
  position: relative;
  padding-left: 30px;
}

.radio-text:before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border: 2px solid rgba(33, 150, 243, 0.3);
  border-radius: 50%;
  transition: all 0.2s;
}

.radio-label input:checked + .radio-text:before {
  border-color: var(--primary-color);
  background-color: rgba(33, 150, 243, 0.1);
}

.radio-text:after {
  content: '';
  position: absolute;
  left: 7px;
  top: 50%;
  transform: translateY(-50%) scale(0);
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--primary-color);
  transition: transform 0.2s;
}

.radio-label input:checked + .radio-text:after {
  transform: translateY(-50%) scale(1);
}

.error-message {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-top: 8px;
  background-color: rgba(255, 82, 82, 0.1);
  border-left: 4px solid var(--error-color);
  color: var(--error-color);
  border-radius: var(--border-radius);
  font-size: 14px;
}

.error-message i {
  margin-right: 8px;
}

.global-error {
  margin-bottom: 20px;
}

.btn i {
  margin-right: 8px;
}
</style>