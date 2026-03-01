<template>
  <div 
    class="inspira-card"
    :class="[variant, { 'hoverable': hoverable }]"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <div v-if="showSpotlight" class="spotlight"></div>
    <div v-if="variant === 'glare'" class="glare-overlay"></div>
    <div class="card-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  variant: {
    type: String,
    default: 'default', // default, spotlight, glare, flip, direction-aware
    validator: (v) => ['default', 'spotlight', 'glare', 'flip', 'direction-aware'].includes(v)
  },
  hoverable: {
    type: Boolean,
    default: true
  }
})

const showSpotlight = ref(false)

const handleMouseEnter = (e) => {
  if (showSpotlight.value) {
    const card = e.currentTarget
    const rect = card.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    card.style.setProperty('--x', `${x}px`)
    card.style.setProperty('--y', `${y}px`)
  }
}

const handleMouseLeave = () => {
  showSpotlight.value = false
}
</script>

<style scoped>
.inspira-card {
  position: relative;
  background: white;
  border-radius: 16px;
  padding: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Default */
.inspira-card.default {
  border: 1px solid #e2e8f0;
}

.inspira-card.default:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

/* Spotlight Card */
.inspira-card.spotlight {
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.inspira-card.spotlight::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
}

.inspira-card.spotlight .spotlight {
  position: absolute;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  transform: translate(-50%, -50%);
  left: var(--x, 50%);
  top: var(--y, 50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.inspira-card.spotlight:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.2);
}

.inspira-card.spotlight:hover .spotlight {
  opacity: 1;
}

/* Glare Card */
.inspira-card.glare {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
}

.inspira-card.glare .glare-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.05) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.inspira-card.glare:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.inspira-card.glare:hover .glare-overlay {
  transform: translateX(100%);
}

/* Flip Card */
.inspira-card.flip {
  perspective: 1000px;
}

.inspira-card.flip .card-content {
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.inspira-card.flip:hover .card-content {
  transform: rotateY(180deg);
}

/* Direction Aware Hover */
.inspira-card.direction-aware {
  transform-style: preserve-3d;
}

.inspira-card.direction-aware:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.25);
}

.card-content {
  position: relative;
  z-index: 1;
}
</style>
