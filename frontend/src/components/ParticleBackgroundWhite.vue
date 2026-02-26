<template>
  <div ref="containerRef" class="particle-bg-white"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const containerRef = ref<HTMLElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let group: THREE.Group
let animationId: number

// Mouse tracking
let mouseX = 0
let mouseY = 0

const initScene = () => {
  if (!containerRef.value) return

  const width = window.innerWidth
  const height = window.innerHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xffffff)

  camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 10000)
  camera.position.z = 500

  renderer = new THREE.WebGLRenderer({ 
    antialias: true,
    alpha: true
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0xffffff, 1)
  containerRef.value.appendChild(renderer.domElement)

  createFloatingCubes()
  
  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', onMouseMove)
}

const createFloatingCubes = () => {
  group = new THREE.Group()
  
  const count = 250
  
  for (let i = 0; i < count; i++) {
    const cubeSize = 40 + Math.random() * 100
    const geometry = new THREE.BoxGeometry(cubeSize, cubeSize, cubeSize)
    
    const material = new THREE.MeshNormalMaterial({
      wireframe: Math.random() > 0.7,
      transparent: true,
      opacity: 0.08 + Math.random() * 0.1
    })
    
    const mesh = new THREE.Mesh(geometry, material)
    
    const farDist = 10000 / 3
    mesh.position.x = (Math.random() - 0.5) * farDist * 2
    mesh.position.y = (Math.random() - 0.5) * farDist * 2
    mesh.position.z = (Math.random() - 0.5) * farDist
    
    const tau = Math.PI * 2
    mesh.rotation.x = Math.random() * tau
    mesh.rotation.y = Math.random() * tau
    mesh.rotation.z = Math.random() * tau
    
    mesh.matrixAutoUpdate = false
    mesh.updateMatrix()
    
    group.add(mesh)
  }
  
  scene.add(group)
}

const onResize = () => {
  if (!containerRef.value) return
  const width = window.innerWidth
  const height = window.innerHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

const onMouseMove = (e: MouseEvent) => {
  mouseX = (e.clientX - window.innerWidth / 2) * 10
  mouseY = (e.clientY - window.innerHeight / 2) * 10
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  const time = Date.now() * 0.0003
  
  // Camera follows mouse smoothly - creates 360 degree rotation effect
  camera.position.x += (mouseX - camera.position.x) * 0.02
  camera.position.y += (-mouseY - camera.position.y) * 0.02
  camera.lookAt(scene.position)
  
  // Rotate entire group slowly
  if (group) {
    const rx = Math.sin(time * 0.4) * 0.1
    const ry = Math.sin(time * 0.2) * 0.1
    const rz = Math.sin(time * 0.1) * 0.1
    group.rotation.x = rx
    group.rotation.y = ry
    group.rotation.z = rz
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
  if (group) {
    group.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose()
        if (obj.material instanceof THREE.Material) {
          obj.material.dispose()
        }
      }
    })
  }
})
</script>

<style scoped lang="scss">
.particle-bg-white {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  background: #ffffff;
}
</style>
