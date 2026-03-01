<template>
  <TransitionGroup 
    name="animated-list" 
    tag="ul" 
    class="animated-list"
    :class="variant"
  >
    <slot />
  </TransitionGroup>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'fade', // fade, slide, scale, stagger
    validator: (v) => ['fade', 'slide', 'scale', 'stagger'].includes(v)
  }
})
</script>

<style scoped>
.animated-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

/* Fade */
.animated-list.fade-enter-active,
.animated-list.fade-leave-active {
  transition: all 0.4s ease;
}

.animated-list.fade-enter-from {
  opacity: 0;
}

.animated-list.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* Slide */
.animated-list.slide-enter-active,
.animated-list.slide-leave-active {
  transition: all 0.4s ease;
}

.animated-list.slide-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.animated-list.slide-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* Scale */
.animated-list.scale-enter-active,
.animated-list.scale-leave-active {
  transition: all 0.4s ease;
}

.animated-list.scale-enter-from,
.animated-list.scale-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* Stagger */
.animated-list.stagger-enter-active {
  transition: all 0.5s ease;
  transition-delay: 0.1s;
}

.animated-list.stagger-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.animated-list.stagger-leave-active {
  transition: all 0.3s ease;
}

.animated-list.stagger-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.animated-list.stagger-move {
  transition: transform 0.4s ease;
}
</style>
