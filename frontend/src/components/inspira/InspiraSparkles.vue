<template>
  <div class="sparkles-container" ref="container">
    <canvas ref="canvas"></canvas>
    <div class="sparkles-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const container = ref(null)
const canvas = ref(null)
let animationId = null

const props = defineProps({
  density: {
    type: Number,
    default: 100
  },
  opacity: {
    type: Number,
    default: 0.5
  },
  speed: {
    type: Number,
    default: 1
  },
  color: {
    type: String,
    default: '#ffffff'
  },
  background: {
    type: String,
    default: 'transparent'
  }
})

onMounted(() => {
  initSparkles()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})

function initSparkles() {
  const cvs = canvas.value
  const ctx = cvs.getContext('2d')
  const rect = container.value.getBoundingClientRect()
  
  cvs.width = rect.width
  cvs.height = rect.height
  
  const particles = []
  
  for (let i = 0; i < props.density; i++) {
    particles.push(createParticle(cvs.width, cvs.height))
  }
  
  function createParticle(w, h) {
    return {
      x: Math.random() * w,
      y: Math.random() * h,
      size: Math.random() * 2 + 0.5,
      speedX: (Math.random() - 0.5) * props.speed * 0.5,
      speedY: -Math.random() * props.speed - 0.5,
      opacity: Math.random() * props.opacity
    }
  }
  
  function animate() {
    ctx.clearRect(0, 0, cvs.width, cvs.height)
    
    particles.forEach(p => {
      p.x += p.speedX
      p.y += p.speedY
      
      // Reset particle when it goes off screen
      if (p.y < -10) {
        p.y = cvs.height + 10
        p.x = Math.random() * cvs.width
      }
      if (p.x < -10) p.x = cvs.width + 10
      if (p.x > cvs.width + 10) p.x = -10
      
      // Draw particle
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = props.color
      ctx.globalAlpha = p.opacity
      ctx.fill()
    })
    
    animationId = requestAnimationFrame(animate)
  }
  
  animate()
}
</script>

<style scoped>
.sparkles-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.sparkles-content {
  position: relative;
  z-index: 1;
}
</style>
