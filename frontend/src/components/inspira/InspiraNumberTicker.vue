<template>
  <span class="number-ticker" ref="tickerRef">
    <span v-for="(digit, index) in displayDigits" :key="index" class="digit">
      {{ digit }}
    </span>
    <span v-if="suffix" class="suffix">{{ suffix }}</span>
  </span>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 1500
  },
  suffix: {
    type: String,
    default: ''
  },
  decimals: {
    type: Number,
    default: 0
  }
})

const displayValue = ref(0)
const tickerRef = ref(null)

const displayDigits = computed(() => {
  const formatted = displayValue.value.toFixed(props.decimals)
  return formatted.toString().split('')
})

watch(() => props.value, (newVal) => {
  animateValue(displayValue.value, newVal)
})

onMounted(() => {
  animateValue(0, props.value)
})

function animateValue(start, end) {
  const startTime = performance.now()
  const diff = end - start
  
  function update(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / props.duration, 1)
    
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3)
    displayValue.value = start + diff * eased
    
    if (progress < 1) {
      requestAnimationFrame(update)
    } else {
      displayValue.value = end
    }
  }
  
  requestAnimationFrame(update)
}
</script>

<style scoped>
.number-ticker {
  display: inline-flex;
  align-items: baseline;
  font-variant-numeric: tabular-nums;
}

.digit {
  display: inline-block;
  min-width: 0.5em;
  text-align: right;
  transition: transform 0.1s ease;
}

.suffix {
  margin-left: 4px;
  font-size: 0.6em;
  color: #64748b;
}
</style>
