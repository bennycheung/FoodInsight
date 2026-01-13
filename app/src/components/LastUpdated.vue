<template>
  <span class="flex items-center gap-1">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span v-if="timestamp">Last updated: {{ formattedTime }}</span>
    <span v-else>Never updated</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  timestamp: Date | null
}>()

const formattedTime = computed(() => {
  if (!props.timestamp) return ''

  const now = new Date()
  const diff = now.getTime() - props.timestamp.getTime()
  const seconds = Math.floor(diff / 1000)

  // If less than 10 seconds ago
  if (seconds < 10) {
    return 'just now'
  }

  // If less than 1 minute ago, show seconds
  if (seconds < 60) {
    return `${seconds}s ago`
  }

  // If less than 1 hour ago, show minutes
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}m ago`
  }

  // Otherwise show time
  return props.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  })
})
</script>
