<template>
  <div class="question-item">
    <div class="question-header">
      <div class="question-number">{{ questionNumber }}</div>
      <div class="question-text">{{ questionText }}</div>
    </div>
    
    <div class="options">
      <div 
        v-for="(option, index) in options" 
        :key="index"
        class="option"
        :class="{ 'selected': selectedOption === option.score }"
        @click="selectOption(option.score)"
      >
        <div class="option-select-indicator">
          <i v-if="selectedOption === option.score" class="fas fa-check-circle"></i>
          <i v-else class="far fa-circle"></i>
        </div>
        <div class="option-text">{{ option.text }}</div>
        <div class="option-highlight"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuestionItem',
  props: {
    questionNumber: {
      type: Number,
      required: true
    },
    questionText: {
      type: String,
      required: true
    },
    options: {
      type: Array,
      required: true
    },
    value: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      selectedOption: this.value
    };
  },
  watch: {
    value(newValue) {
      this.selectedOption = newValue;
    }
  },
  methods: {
    selectOption(score) {
      this.selectedOption = score;
      this.$emit('update:value', score);
      this.$emit('answer', {
        questionNumber: this.questionNumber,
        answer: score
      });
    }
  }
}
</script>

<style scoped>
.question-item {
  background-color: white;
  border-radius: var(--border-radius);
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: var(--box-shadow);
  border: 1px solid rgba(33, 150, 243, 0.1);
  position: relative;
  overflow: hidden;
  transition: transform var(--transition-speed), box-shadow var(--transition-speed);
}

.question-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(33, 150, 243, 0.15);
}

.question-header {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.question-number {
  width: 30px;
  height: 30px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-right: 15px;
  flex-shrink: 0;
  font-family: var(--heading-font);
  box-shadow: 0 2px 10px rgba(33, 150, 243, 0.3);
}

.question-text {
  font-size: 18px;
  line-height: 1.5;
  color: var(--text-primary);
  font-weight: 500;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: var(--border-radius);
  background-color: rgba(33, 150, 243, 0.03);
  cursor: pointer;
  transition: all var(--transition-speed);
  position: relative;
  overflow: hidden;
}

.option:hover {
  background-color: rgba(33, 150, 243, 0.08);
}

.option.selected {
  background-color: rgba(33, 150, 243, 0.12);
}

.option-select-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-right: 16px;
  color: var(--primary-color);
  font-size: 24px;
  transition: transform 0.3s;
}

.option.selected .option-select-indicator {
  transform: scale(1.2);
}

.option.selected .option-select-indicator i {
  animation: pulse 1s;
}

.option-text {
  font-size: 16px;
  color: var(--text-primary);
  flex: 1;
  transition: transform 0.3s;
}

.option.selected .option-text {
  font-weight: 500;
  color: var(--primary-dark);
}

.option-highlight {
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: transparent;
  transition: background-color 0.3s;
}

.option.selected .option-highlight {
  background-color: var(--primary-color);
}
</style>