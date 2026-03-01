<template>
  <div class="bento-grid" :class="[`cols-${cols}`, `gap-${gap}`]">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  cols: {
    type: Number,
    default: 3
  },
  gap: {
    type: String,
    default: 'md', // sm, md, lg
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})
</script>

<style scoped>
.bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.cols-2 { grid-template-columns: repeat(2, 1fr); }
.cols-3 { grid-template-columns: repeat(3, 1fr); }
.cols-4 { grid-template-columns: repeat(4, 1fr); }

.gap-sm { gap: 12px; }
.gap-md { gap: 20px; }
.gap-lg { gap: 28px; }

@media (max-width: 768px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
}
</style>
