<template>
  <div
    class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-white"
    :class="badgeClass"
    :aria-label="ariaLabel"
    role="status"
  >
    <!-- Checkmark Icon (Available) -->
    <svg
      v-if="status === 'available'"
      class="w-3 h-3"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden="true"
    >
      <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
    </svg>

    <!-- Lightning Bolt Icon (Low Stock) -->
    <svg
      v-else-if="status === 'low'"
      class="w-3 h-3"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden="true"
    >
      <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"/>
    </svg>

    <!-- X Mark Icon (Out of Stock) -->
    <svg
      v-else-if="status === 'out'"
      class="w-3 h-3"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden="true"
    >
      <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/>
    </svg>

    <!-- Star Icon (Just Restocked) -->
    <svg
      v-else-if="status === 'restocked'"
      class="w-3 h-3"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden="true"
    >
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
    </svg>

    <span>{{ statusText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type StatusType = 'available' | 'low' | 'out' | 'restocked'

const props = defineProps<{
  status: StatusType
  count: number
}>()

// Badge styling based on status
const badgeClass = computed(() => {
  switch (props.status) {
    case 'available':
      return 'bg-status-available'
    case 'low':
      return 'bg-status-low'
    case 'out':
      return 'bg-status-empty'
    case 'restocked':
      return 'bg-status-restocked'
    default:
      return 'bg-status-available'
  }
})

// Status text
const statusText = computed(() => {
  switch (props.status) {
    case 'available':
      return 'Available'
    case 'low':
      return 'Low'
    case 'out':
      return 'Empty'
    case 'restocked':
      return 'Back in stock!'
    default:
      return 'Available'
  }
})

// ARIA label for screen readers
const ariaLabel = computed(() => {
  switch (props.status) {
    case 'available':
      return `${props.count} items available`
    case 'low':
      return `Only ${props.count} items left`
    case 'out':
      return 'Out of stock'
    case 'restocked':
      return `Back in stock! ${props.count} available`
    default:
      return `${props.count} items available`
  }
})
</script>
