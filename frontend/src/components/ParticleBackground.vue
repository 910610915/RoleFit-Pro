<template>
  <div ref="containerRef" class="particle-background"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const containerRef = ref<HTMLElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let particles: THREE.Points
let stars: THREE.Points
let animationId: number

const mouse = {
  x: 0,
  y: 0,
  targetX: 0,
  targetY: 0
}

const initScene = () => {
  if (!containerRef.value) return

  const width = window.innerWidth
  const height = window.innerHeight

  // Scene - dark space
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x000000, 0.0015)

  // Camera
  camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 2000)
  camera.position.z = 150

  // Renderer
  renderer = new THREE.WebGLRenderer({ 
    antialias: true, 
    alpha: true 
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x000000, 0)
  containerRef.value.appendChild(renderer.domElement)

  // Create floating particles (larger, slower)
  createFloatingParticles()
  
  // Create star field (tiny background stars)
  createStarField()
  
  // Event listeners
  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', onMouseMove)
}

const createFloatingParticles = () => {
  const particleCount = 500
  const positions = new Float32Array(particleCount * 3)
  const colors = new Float32Array(particleCount * 3)
  const sizes = new Float32Array(particleCount)
  const speeds = new Float32Array(particleCount)
  
  // Unique color palette - warm, distinctive colors (not AI blue-purple)
  const colorPalette = [
    new THREE.Color(0xff6b6b), // Coral red
    new THREE.Color(0xfeca57), // Warm yellow
    new THREE.Color(0x48dbfb), // Sky blue
    new THREE.Color(0xff9ff3), // Pink
    new THREE.Color(0x54a0ff), // Royal blue
    new THREE.Color(0x5f27cd), // Deep purple
    new THREE.Color(0x00d2d3), // Teal
    new THREE.Color(0xffeaa7), // Cream yellow
  ]

  for (let i = 0; i < particleCount; i++) {
    const i3 = i * 3
    
    // Spread in 3D space - wider distribution
    positions[i3] = (Math.random() - 0.5) * 400
    positions[i3 + 1] = (Math.random() - 0.5) * 400
    positions[i3 + 2] = (Math.random() - 0.5) * 400
    
    // Color - random from warm/distinctive palette
    const color = colorPalette[Math.floor(Math.random() * colorPalette.length)]
    colors[i3] = color.r
    colors[i3 + 1] = color.g
    colors[i3 + 2] = color.b
    
    // Size - varying
    sizes[i] = Math.random() * 8 + 2
    
    // Speed - for individual animation
    speeds[i] = Math.random() * 0.5 + 0.1
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
  geometry.setAttribute('speed', new THREE.BufferAttribute(speeds, 1))

  // Custom shader for floating glow effect
  const material = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uPixelRatio: { value: renderer.getPixelRatio() }
    },
    vertexShader: `
      attribute float size;
      attribute float speed;
      varying vec3 vColor;
      varying float vSpeed;
      uniform float uTime;
      uniform float uPixelRatio;
      
      void main() {
        vColor = color;
        vSpeed = speed;
        
        vec3 pos = position;
        
        // Floating animation - up and down
        pos.y += sin(uTime * speed + position.x * 0.01) * 15.0;
        pos.x += cos(uTime * speed * 0.5 + position.y * 0.01) * 8.0;
        
        // Slight rotation
        float angle = uTime * 0.02;
        pos.x = pos.x * cos(angle) - pos.z * sin(angle);
        pos.z = pos.x * sin(angle) + pos.z * cos(angle);
        
        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_PointSize = size * uPixelRatio * (80.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying float vSpeed;
      
      void main() {
        float dist = length(gl_PointCoord - vec2(0.5));
        if (dist > 0.5) discard;
        
        // Soft glow with varying intensity
        float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
        alpha *= 0.7;
        
        gl_FragColor = vec4(vColor, alpha);
      }
    `,
    transparent: true,
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  })

  particles = new THREE.Points(geometry, material)
  scene.add(particles)
}

const createStarField = () => {
  const starCount = 2000
  const positions = new Float32Array(starCount * 3)
  const sizes = new Float32Array(starCount)
  
  for (let i = 0; i < starCount; i++) {
    const i3 = i * 3
    
    // Distant stars
    positions[i3] = (Math.random() - 0.5) * 1000
    positions[i3 + 1] = (Math.random() - 0.5) * 1000
    positions[i3 + 2] = (Math.random() - 0.5) * 1000 - 200
    
    sizes[i] = Math.random() * 1.5 + 0.5
  }
  
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
  
  const material = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 1,
    transparent: true,
    opacity: 0.6,
    sizeAttenuation: true
  })
  
  stars = new THREE.Points(geometry, material)
  scene.add(stars)
}

const onResize = () => {
  if (!containerRef.value) return
  
  const width = window.innerWidth
  const height = window.innerHeight
  
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

const onMouseMove = (event: MouseEvent) => {
  mouse.targetX = (event.clientX / window.innerWidth) * 2 - 1
  mouse.targetY = -(event.clientY / window.innerHeight) * 2 + 1
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  const time = performance.now() * 0.001
  
  // Update shader uniform
  if (particles && particles.material instanceof THREE.ShaderMaterial) {
    particles.material.uniforms.uTime.value = time
  }
  
  // Smooth mouse follow
  mouse.x += (mouse.targetX - mouse.x) * 0.02
  mouse.y += (mouse.targetY - mouse.y) * 0.02
  
  // Gentle camera movement based on mouse
  camera.position.x = mouse.x * 20
  camera.position.y = mouse.y * 20
  camera.lookAt(scene.position)
  
  // Slowly rotate star field
  if (stars) {
    stars.rotation.y = time * 0.01
    stars.rotation.x = time * 0.005
  }
  
  // Slowly rotate particles
  if (particles) {
    particles.rotation.y = time * 0.03 + mouse.x * 0.1
    particles.rotation.x = time * 0.02 + mouse.y * 0.1
  }
  
  renderer.render(scene, camera)
}

onMounted(() => {
  initScene()
  animate()
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('mousemove', onMouseMove)
  
  if (renderer) {
    renderer.dispose()
  }
  if (particles) {
    particles.geometry.dispose()
    if (particles.material instanceof THREE.Material) {
      particles.material.dispose()
    }
  }
  if (stars) {
    stars.geometry.dispose()
    if (stars.material instanceof THREE.Material) {
      stars.material.dispose()
    }
  }
})
</script>

<style scoped lang="scss">
.particle-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  background: radial-gradient(ellipse at center, #0a0a12 0%, #000000 100%);
}
</style>
