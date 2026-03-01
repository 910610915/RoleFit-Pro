<template>
  <button
    class="rainbow-button"
    :class="[size]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  size: {
    type: String,
    default: 'md'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style scoped>
.rainbow-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  cursor: pointer;
  border: none;
  outline: none;
  transition: all 0.3s ease;
  color: white;
  overflow: hidden;
  
  /* Rainbow gradient background */
  background: linear-gradient(
    to right,
    #ff6b6b,
    #feca57,
    #48dbfb,
    #ff9ff3,
    #54a0ff,
    #ff6b6b
  );
  background-size: 300% 300%;
  animation: rainbow-flow 3s ease infinite;
  
  /* Rounded corners - always round */
  border-radius: 12px;
  
  /* Shadow */
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.rainbow-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

.rainbow-button:active:not(:disabled) {
  transform: translateY(0);
}

.rainbow-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Sizes */
.rainbow-button.sm {
  padding: 8px 16px;
  font-size: 12px;
  border-radius: 8px;
}

.rainbow-button.md {
  padding: 12px 24px;
  font-size: 14px;
  border-radius: 12px;
}

.rainbow-button.lg {
  padding: 16px 32px;
  font-size: 16px;
  border-radius: 14px;
}

@keyframes rainbow-flow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>
