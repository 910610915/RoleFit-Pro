<script setup lang="ts">
interface AuroraBackgroundProps {
  class?: string;
}

defineProps<AuroraBackgroundProps>();
</script>

<template>
  <div class="aurora-wrapper relative w-full min-h-screen">
    <div class="aurora-bg absolute inset-0 overflow-hidden pointer-events-none">
      <div
        class="aurora-gradient animate-aurora absolute -inset-[10px]"
        :style="{
          backgroundImage: 'linear-gradient(100deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 7%, transparent 10%, transparent 12%, rgba(255,255,255,0) 16%), repeating-linear-gradient(100deg, #3b82f6 10%, #a5b4fc 15%, #93c5fd 20%, #ddd6fe 25%, #60a5fa 30%)',
          backgroundSize: '300% 200%',
          backgroundPosition: '50% 50%, 50% 50%',
          filter: 'blur(30px) brightness(1.2)',
          opacity: 0.6,
        }"
      />
      <!-- Second layer for depth -->
      <div
        class="aurora-gradient-2 animate-aurora-2 absolute -inset-[10px]"
        :style="{
          backgroundImage: 'repeating-linear-gradient(100deg, #8b5cf6 10%, #a78bfa 20%, #c4b5fd 30%, #ddd6fe 40%, #7c3aed 50%)',
          backgroundSize: '400% 300%',
          backgroundPosition: '0% 0%',
          filter: 'blur(40px)',
          opacity: 0.4,
        }"
      />
    </div>
    <slot />
  </div>
</template>

<style scoped>
@keyframes aurora {
  0% {
    background-position: 50% 50%, 50% 50%;
  }
  50% {
    background-position: 50% 50%, 100% 100%;
  }
  100% {
    background-position: 50% 50%, 50% 50%;
  }
}

@keyframes aurora-2 {
  0%, 100% {
    background-position: 0% 0%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.animate-aurora {
  animation: aurora 20s linear infinite;
}

.animate-aurora-2 {
  animation: aurora-2 25s linear infinite reverse;
}
</style>
