<template>
  <Transition name="slide">
    <div
      v-if="needRefresh"
      class="fixed bottom-16 left-4 right-4 bg-blue-600 text-white rounded-lg shadow-lg p-4"
    >
      <p class="text-sm mb-2">A new version is available!</p>
      <div class="flex gap-2">
        <button
          @click="updateServiceWorker(true)"
          class="px-3 py-1 bg-white text-blue-600 rounded text-sm font-medium"
        >
          Update
        </button>
        <button
          @click="close"
          class="px-3 py-1 text-blue-100 text-sm"
        >
          Later
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useRegisterSW } from 'virtual:pwa-register/vue'

const {
  needRefresh,
  updateServiceWorker
} = useRegisterSW()

const close = () => {
  needRefresh.value = false
}
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
