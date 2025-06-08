<template>
  <div class="page-container questionnaire-page">
    <nav-bar title="心理测评" />
    
    <div class="section-header">
      <i class="fas fa-clipboard-list section-icon"></i>
      <h2>选择测评量表</h2>
    </div>
    
    <div class="scale-section">
      <scale-selector 
        :scales="scales"
        v-model="selectedScale"
        @scale-selected="onScaleSelected"
      />
      
      <div v-if="selectedScale && !questions.length" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载量表问题中...</p>
      </div>
    </div>
    
    <div class="section-header">
      <i class="fas fa-image section-icon"></i>
      <h2>上传绘画图片 <span class="optional-tag">(可选)</span></h2>
    </div>
    
    <div class="image-upload-section">
      <div class="upload-container" @click="triggerFileInput">
        <input 
          type="file"
          ref="fileInput"
          accept="image/*"
          @change="onFileSelected"
          class="file-input"
        />
        
        <div v-if="!imagePreview" class="upload-placeholder">
          <div class="upload-icon">
            <i class="fas fa-cloud-upload-alt"></i>
          </div>
          <div>点击上传图片</div>
        </div>
        
        <div v-else class="image-preview-container">
          <img :src="imagePreview" alt="Preview" class="image-preview" />
          <div class="remove-image" @click.stop="removeImage">
            <i class="fas fa-times"></i>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="questions.length" class="section-header">
      <i class="fas fa-question-circle section-icon"></i>
      <h2>问卷内容</h2>
    </div>
    
    <div v-if="questions.length" class="questions-section">
      <question-item
        v-for="question in questions"
        :key="question.number"
        :questionNumber="question.number"
        :questionText="question.text"
        :options="question.options"
        :value="answers['q' + question.number]"
        @answer="onAnswer"
      />
    </div>
    
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      {{ error }}
    </div>
    
    <div class="action-buttons">
      <button 
        class="btn btn-block" 
        @click="submitQuestionnaire"
        :disabled="!canSubmit || loading"
      >
        <i class="fas fa-paper-plane"></i>
        {{ loading ? '提交中...' : '提交测评' }}
      </button>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions, mapGetters } from 'vuex';
import NavBar from '../components/NavBar.vue';
import ScaleSelector from '../components/ScaleSelector.vue';
import QuestionItem from '../components/QuestionItem.vue';

export default {
  name: 'QuestionnaireView',
  components: {
    NavBar,
    ScaleSelector,
    QuestionItem
  },
  data() {
    return {
      selectedScale: '',
      imageFile: null,
      imagePreview: null,
      loading: false,
      error: ''
    };
  },
  computed: {
    ...mapState({
      scales: state => state.scales,
      questions: state => state.scaleQuestions,
      storeError: state => state.error,
      submissionId: state => state.assessment.submissionId
    }),
    ...mapGetters(['getAssessmentAnswers']),
    
    answers() {
      return this.getAssessmentAnswers;
    },
    
    canSubmit() {
      return (this.imageFile && !this.selectedScale) || 
             (this.selectedScale && Object.keys(this.answers).length > 0);
    }
  },
  watch: {
    storeError(newError) {
      if (newError) {
        this.error = newError;
      }
    },
    
    submissionId(newId) {
      if (newId) {
        this.$router.push('/loading');
      }
    }
  },
  methods: {
    ...mapActions([
      'fetchScales', 
      'fetchScaleQuestions', 
      'setAnswer', 
      'setUploadedImage',
      'submitAssessment',
      'clearError'
    ]),
    
    async onScaleSelected(scaleCode) {
      if (scaleCode) {
        try {
          await this.fetchScaleQuestions(scaleCode);
        } catch (error) {
          this.error = '加载量表问题失败，请重试';
        }
      }
    },
    
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    
    onFileSelected(event) {
      const files = event.target.files;
      if (!files.length) return;
      
      const file = files[0];
      
      if (!file.type.match('image.*')) {
        this.error = '请上传图片文件';
        return;
      }
      
      if (file.size > 5 * 1024 * 1024) {
        this.error = '图片大小不能超过5MB';
        return;
      }
      
      this.imageFile = file;
      this.setUploadedImage(file);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        this.imagePreview = e.target.result;
      };
      reader.readAsDataURL(file);
    },
    
    removeImage(event) {
      event.stopPropagation();
      this.imageFile = null;
      this.imagePreview = null;
      this.setUploadedImage(null);
      this.$refs.fileInput.value = '';
    },
    
    onAnswer({ questionNumber, answer }) {
      this.setAnswer({ questionNumber, answer });
    },
    
    async submitQuestionnaire() {
      if (!this.canSubmit) {
        this.error = '请上传图片或选择量表并回答至少一个问题';
        return;
      }
      
      this.loading = true;
      this.error = '';
      
      try {
        await this.submitAssessment();
      } catch (error) {
        this.error = error.response?.data?.detail || '提交测评失败，请重试';
        this.loading = false;
      }
    }
  },
  async created() {
    this.clearError();
    
    try {
      await this.fetchScales();
    } catch (error) {
      this.error = '加载量表失败';
    }
    
    if (this.$store.state.currentScale) {
      this.selectedScale = this.$store.state.currentScale;
      this.onScaleSelected(this.selectedScale);
    }
  }
}
</script>

<style scoped>
.questionnaire-page {
  padding-top: 70px;
  padding-bottom: 40px;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 16px;
}

.section-icon {
  font-size: 24px;
  color: var(--primary-color);
  margin-right: 12px;
}

h2 {
  margin: 0;
  font-size: 20px;
  color: var(--primary-color);
  font-family: var(--heading-font);
}

.optional-tag {
  font-size: 14px;
  color: var(--text-secondary);
  opacity: 0.7;
  font-weight: normal;
  font-family: var(--body-font);
}

.scale-section,
.image-upload-section,
.questions-section {
  margin-bottom: 40px;
  padding: 0 16px;
}

.upload-container {
  border: 2px dashed rgba(33, 150, 243, 0.3);
  border-radius: var(--border-radius);
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-speed);
  background-color: rgba(255, 255, 255, 0.7);
}

.upload-container:hover {
  border-color: var(--primary-color);
  background-color: rgba(33, 150, 243, 0.05);
  transform: translateY(-5px);
}

.file-input {
  display: none;
}

.upload-placeholder {
  color: var(--text-secondary);
}

.upload-icon {
  font-size: 40px;
  margin-bottom: 16px;
  color: var(--primary-color);
  opacity: 0.7;
}

.image-preview-container {
  position: relative;
  display: inline-block;
}

.image-preview {
  max-width: 100%;
  max-height: 200px;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
}

.remove-image {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 30px;
  height: 30px;
  background-color: var(--error-color);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform var(--transition-speed);
}

.remove-image:hover {
  transform: scale(1.1);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 30px 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(33, 150, 243, 0.1);
  border-top: 4px solid var(--primary-color);
  border-radius: 50%;
  animation: rotate 1s linear infinite;
  margin-bottom: 16px;
}

.error-message {
  display: flex;
  align-items: center;
  padding: 16px;
  margin: 20px 16px;
  background-color: rgba(255, 82, 82, 0.1);
  border-left: 4px solid var(--error-color);
  color: var(--error-color);
  border-radius: var(--border-radius);
}

.error-message i {
  margin-right: 10px;
  font-size: 18px;
}

.action-buttons {
  margin: 40px 16px;
}

.btn i {
  margin-right: 8px;
}
</style>