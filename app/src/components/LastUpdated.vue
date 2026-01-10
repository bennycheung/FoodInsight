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

  // If less than 1 minute ago
  if (diff < 60000) {
    return 'Just now'
  }

  // If less than 1 hour ago, show minutes
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  }

  // Otherwise show time
  return props.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  })
})
</script>
