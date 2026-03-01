<template>
  <div class="relative flex min-h-96 w-full items-center justify-center text-xl" style="height: 400px;">
    <span class="hidden md:block">Move your mouse around</span>
    <span class="block md:hidden">Swipe anywhere to see the cursor</span>
    <SleekLineCursorGlobal />
  </div>
</template>

<script setup>
import SleekLineCursorGlobal from './SleekLineCursorGlobal.vue'
</script>
