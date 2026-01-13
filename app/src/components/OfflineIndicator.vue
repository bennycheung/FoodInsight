<template>
  <Transition name="slide-down">
    <div
      v-if="!isOnline"
      class="offline-banner"
      role="alert"
      aria-live="polite"
    >
      <!-- Cloud Offline Icon -->
      <svg
        class="w-5 h-5 flex-shrink-0"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
        />
      </svg>
      <span class="font-medium">You're offline - showing last known snacks</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useOnline } from '@vueuse/core'

const isOnline = useOnline()
</script>

<style scoped>
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(145deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  font-size: 0.875rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Slide down animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 250ms ease-out, opacity 250ms ease-out;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
