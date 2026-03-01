<template>
  <Teleport to="body">
    <div class="sleek-cursor-wrapper" :class="{ visible: isVisible }">
      <!-- Mouse trail effect -->
      <svg class="cursor-svg" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="cursorGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#8b5cf6;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" />
          </linearGradient>
        </defs>
        <!-- Main circle -->
        <circle
          v-if="isVisible"
          :cx="mousePosition.x"
          :cy="mousePosition.y"
          r="12"
          fill="url(#cursorGradient)"
          class="cursor-circle"
        />
        <!-- Horizontal line -->
        <line
          v-if="isVisible"
          :x1="mousePosition.x - 25"
          :y1="mousePosition.y"
          :x2="mousePosition.x + 25"
          :y2="mousePosition.y"
          stroke="url(#cursorGradient)"
          stroke-width="1.5"
          stroke-linecap="round"
          class="cursor-line"
        />
        <!-- Vertical line -->
        <line
          v-if="isVisible"
          :x1="mousePosition.x"
          :y1="mousePosition.y - 25"
          :x2="mousePosition.x"
          :y2="mousePosition.y + 25"
          stroke="url(#cursorGradient)"
          stroke-width="1.5"
          stroke-linecap="round"
          class="cursor-line"
        />
      </svg>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Teleport } from 'vue'

const mousePosition = ref({ x: -100, y: -100 })
const isVisible = ref(false)

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove, { passive: true })
  document.addEventListener('mouseenter', handleMouseEnter, { passive: true })
  document.addEventListener('mouseleave', handleMouseLeave, { passive: true })
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseenter', handleMouseEnter)
  document.removeEventListener('mouseleave', handleMouseLeave)
})

function handleMouseMove(e) {
  mousePosition.value = {
    x: e.clientX,
    y: e.clientY
  }
  if (!isVisible.value) {
    isVisible.value = true
  }
}

function handleMouseEnter() {
  isVisible.value = true
}

function handleMouseLeave() {
  isVisible.value = false
  // Move cursor off screen when hidden
  mousePosition.value = { x: -100, y: -100 }
}
</script>

<style scoped>
.sleek-cursor-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 2147483647;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sleek-cursor-wrapper.visible {
  opacity: 1;
}

.cursor-svg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.cursor-circle {
  filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.8));
  transition: r 0.15s ease-out;
}

.cursor-line {
  opacity: 0.8;
  transition: all 0.1s ease-out;
}
</style>
