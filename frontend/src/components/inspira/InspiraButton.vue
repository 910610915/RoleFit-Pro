<template>
  <button
    :class="[
      'inspira-button',
      variant,
      size,
      { 'loading': loading }
    ]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span class="button-content">
      <slot />
    </span>
    <span v-if="loading" class="loader"></span>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary', // primary, secondary, gradient, shimmer, rainbow, ripple
    validator: (v) => ['primary', 'secondary', 'gradient', 'shimmer', 'rainbow', 'ripple'].includes(v)
  },
  size: {
    type: String,
    default: 'md', // sm, md, lg
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style scoped>
.inspira-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  border: none;
  outline: none;
}

/* Sizes */
.inspira-button.sm {
  padding: 6px 12px;
  font-size: 12px;
}

.inspira-button.md {
  padding: 10px 20px;
  font-size: 14px;
}

.inspira-button.lg {
  padding: 14px 28px;
  font-size: 16px;
}

/* Primary */
.inspira-button.primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
}

.inspira-button.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

/* Secondary */
.inspira-button.secondary {
  background: #f1f5f9;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.inspira-button.secondary:hover:not(:disabled) {
  background: #e2e8f0;
  transform: translateY(-1px);
}

/* Gradient Button */
.inspira-button.gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  background-size: 200% 200%;
  animation: gradient-shift 3s ease infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.inspira-button.gradient:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
}

/* Shimmer Button */
.inspira-button.shimmer {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
}

.inspira-button.shimmer::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

.inspira-button.shimmer:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

/* Rainbow Button */
.inspira-button.rainbow {
  background: linear-gradient(
    to right,
    #ff6b6b,
    #feca57,
    #48dbfb,
    #ff9ff3,
    #54a0ff
  );
  background-size: 300% 300%;
  color: white;
  animation: rainbow 3s ease infinite;
}

@keyframes rainbow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.inspira-button.rainbow:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

/* Ripple Button */
.inspira-button.ripple {
  background: #3b82f6;
  color: white;
  overflow: hidden;
}

.inspira-button.ripple::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  top: 50%;
  left: 50%;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transform: scale(0);
  transition: transform 0.5s, opacity 0.5s;
}

.inspira-button.ripple:active::after {
  transform: scale(4);
  opacity: 0;
  transition: transform 0s, opacity 0s;
}

.inspira-button.ripple:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

/* Disabled state */
.inspira-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

/* Loading state */
.inspira-button.loading {
  pointer-events: none;
}

.button-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loader {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
