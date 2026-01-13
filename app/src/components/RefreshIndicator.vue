<template>
  <div class="flex items-center gap-3">
    <!-- Circular Progress Ring -->
    <div class="relative">
      <svg
        class="w-10 h-10 transform -rotate-90"
        viewBox="0 0 36 36"
        :class="{ 'refresh-spinning': isRefreshing }"
      >
        <!-- Background circle -->
        <circle
          cx="18"
          cy="18"
          r="15"
          fill="none"
          stroke="#e5e7eb"
          stroke-width="3"
          class="dark:stroke-gray-600"
        />
        <!-- Progress circle -->
        <circle
          v-if="!isRefreshing"
          cx="18"
          cy="18"
          r="15"
          fill="none"
          stroke="#8b5cf6"
          stroke-width="3"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="progressOffset"
          class="transition-all duration-1000 ease-linear"
        />
      </svg>

      <!-- Center content -->
      <div class="absolute inset-0 flex items-center justify-center">
        <!-- Refreshing spinner icon -->
        <svg
          v-if="isRefreshing"
          class="w-5 h-5 text-snack-purple"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>

        <!-- Success checkmark -->
        <svg
          v-else-if="showSuccess"
          class="w-5 h-5 text-fresh-green success-flash"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          @animationend="showSuccess = false"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
        </svg>

        <!-- Error indicator -->
        <svg
          v-else-if="hasError"
          class="w-5 h-5 text-red-500 error-shake"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          @animationend="hasError = false"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>

        <!-- Seconds countdown -->
        <span
          v-else
          class="text-xs font-bold text-gray-700 dark:text-gray-300"
        >
          {{ seconds }}
        </span>
      </div>
    </div>

    <!-- Manual refresh button -->
    <button
      @click="handleRefresh"
      :disabled="isRefreshing"
      class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
      :class="{ 'error-shake': hasError }"
      title="Refresh now"
      aria-label="Refresh inventory"
    >
      <svg
        class="w-5 h-5 text-gray-600 dark:text-gray-400"
        :class="{ 'refresh-spinning': isRefreshing }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  seconds: number
  totalSeconds: number
  isRefreshing: boolean
  error?: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

// Animation states
const showSuccess = ref(false)
const hasError = ref(false)
const wasRefreshing = ref(false)

// SVG circle calculations
const circumference = 2 * Math.PI * 15 // ~94.25

const progressOffset = computed(() => {
  const progress = props.seconds / props.totalSeconds
  return circumference * (1 - progress)
})

// Watch for refresh completion to trigger success animation
watch(
  () => props.isRefreshing,
  (refreshing, wasRefreshingPrev) => {
    if (wasRefreshingPrev && !refreshing) {
      // Refresh just completed
      if (props.error) {
        hasError.value = true
      } else {
        showSuccess.value = true
      }
    }
    wasRefreshing.value = refreshing
  }
)

// Watch for error prop changes
watch(
  () => props.error,
  (error) => {
    if (error) {
      hasError.value = true
    }
  }
)

const handleRefresh = () => {
  emit('refresh')
}
</script>
