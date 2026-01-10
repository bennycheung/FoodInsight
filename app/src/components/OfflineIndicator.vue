<template>
  <Transition name="slide">
    <div
      v-if="!isOnline"
      class="fixed bottom-0 left-0 right-0 bg-yellow-500 text-yellow-900 px-4 py-2 text-center text-sm"
    >
      You're offline. Showing cached data.
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useOnline } from '@vueuse/core'

const isOnline = useOnline()
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateY(100%);
}
</style>
