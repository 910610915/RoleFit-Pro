<template>
  <div class="border-beam" :class="{ 'active': active }">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  active: {
    type: Boolean,
    default: true
  }
})
</script>

<style scoped>
.border-beam {
  position: relative;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.border-beam::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  padding: 2px;
  background: linear-gradient(
    135deg,
    #6366f1,
    #8b5cf6,
    #ec4899,
    #f59e0b,
    #6366f1
  );
  background-size: 400% 400%;
  animation: beam-gradient 4s linear infinite;
  -webkit-mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.border-beam.active::before {
  opacity: 1;
}

.border-beam:hover::before {
  opacity: 1;
}

@keyframes beam-gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>
