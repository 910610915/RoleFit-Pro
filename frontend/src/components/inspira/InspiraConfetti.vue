<template>
  <Teleport to="body">
    <canvas ref="canvas" class="confetti-canvas" v-show="show"></canvas>
  </Teleport>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  particleCount: {
    type: Number,
    default: 150
  },
  colors: {
    type: Array,
    default: () => ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6']
  },
  duration: {
    type: Number,
    default: 3000
  }
})

const canvas = ref(null)
let animationId = null
let particles = []

watch(() => props.show, (newVal) => {
  if (newVal) {
    startConfetti()
    setTimeout(() => {
      stopConfetti()
    }, props.duration)
  }
})

onUnmounted(() => {
  stopConfetti()
})

function startConfetti() {
  const cvs = canvas.value
  if (!cvs) return
  
  cvs.width = window.innerWidth
  cvs.height = window.innerHeight
  
  particles = []
  
  for (let i = 0; i < props.particleCount; i++) {
    particles.push(createParticle())
  }
  
  animate()
}

function createParticle() {
  return {
    x: Math.random() * window.innerWidth,
    y: -20 - Math.random() * 100,
    size: Math.random() * 8 + 4,
    color: props.colors[Math.floor(Math.random() * props.colors.length)],
    speedY: Math.random() * 3 + 2,
    speedX: (Math.random() - 0.5) * 2,
    rotation: Math.random() * 360,
    rotationSpeed: (Math.random() - 0.5) * 10,
    opacity: 1
  }
}

function animate() {
  const cvs = canvas.value
  if (!cvs) return
  
  const ctx = cvs.getContext('2d')
  ctx.clearRect(0, 0, cvs.width, cvs.height)
  
  let activeParticles = 0
  
  particles.forEach(p => {
    p.y += p.speedY
    p.x += p.speedX
    p.rotation += p.rotationSpeed
    
    if (p.y < cvs.height + 20) {
      activeParticles++
      
      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rotation * Math.PI / 180)
      ctx.fillStyle = p.color
      ctx.globalAlpha = p.opacity
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size)
      ctx.restore()
      
      if (p.y > cvs.height * 0.7) {
        p.opacity -= 0.01
      }
    }
  })
  
  if (activeParticles > 0) {
    animationId = requestAnimationFrame(animate)
  }
}

function stopConfetti() {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
}
</script>

<style scoped>
.confetti-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9999;
}
</style>
