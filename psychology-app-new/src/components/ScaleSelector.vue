<template>
  <div class="scale-selector">
    <label for="scale-select">
      <i class="fas fa-clipboard-list icon-left"></i>
      请选择测试量表
    </label>
    <div class="select-wrapper">
      <select 
        id="scale-select" 
        v-model="selectedScale"
        @change="onScaleChange"
      >
        <option value="">请选择一个量表</option>
        <option 
          v-for="scale in scales" 
          :key="scale.code" 
          :value="scale.code"
        >
          {{ scale.name }}
        </option>
      </select>
      <div class="select-arrow">
        <i class="fas fa-chevron-down"></i>
      </div>
    </div>
    <div class="scale-info" v-if="selectedScale">
      <i class="fas fa-info-circle"></i>
      <span>已选择量表: {{ getSelectedScaleName }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScaleSelector',
  props: {
    scales: {
      type: Array,
      required: true
    },
    value: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      selectedScale: this.value
    };
  },
  computed: {
    getSelectedScaleName() {
      if (!this.selectedScale || !this.scales) return '';
      const selectedScale = this.scales.find(scale => scale.code === this.selectedScale);
      return selectedScale ? selectedScale.name : '';
    }
  },
  watch: {
    value(newValue) {
      this.selectedScale = newValue;
    }
  },
  methods: {
    onScaleChange() {
      this.$emit('update:value', this.selectedScale);
      this.$emit('scale-selected', this.selectedScale);
    }
  }
}
</script>

<style scoped>
.scale-selector {
  margin-bottom: 30px;
  background-color: white;
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: var(--box-shadow);
  border: 1px solid rgba(33, 150, 243, 0.1);
  transition: transform var(--transition-speed), box-shadow var(--transition-speed);
}

.scale-selector:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(33, 150, 243, 0.15);
}

.icon-left {
  margin-right: 8px;
  color: var(--primary-color);
}

label {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 16px;
  font-family: var(--heading-font);
}

.select-wrapper {
  position: relative;
  margin-bottom: 16px;
}

select {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid rgba(33, 150, 243, 0.2);
  border-radius: var(--border-radius);
  background-color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  appearance: none;
  transition: all var(--transition-speed);
  color: var(--text-primary);
  font-family: var(--body-font);
  cursor: pointer;
}

select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2);
  outline: none;
}

.select-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--primary-color);
  pointer-events: none;
  transition: transform var(--transition-speed);
}

select:focus + .select-arrow {
  transform: translateY(-50%) rotate(180deg);
}

.scale-info {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background-color: rgba(33, 150, 243, 0.05);
  border-radius: var(--border-radius);
  color: var(--primary-color);
  font-size: 14px;
}

.scale-info i {
  margin-right: 8px;
  animation: pulse 2s infinite;
}
</style>