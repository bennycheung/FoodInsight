<template>
  <div
    class="card-enter rounded-2xl p-4 min-h-[160px] shadow-card flex flex-col items-center text-center bg-gray-50 dark:bg-gray-800"
    :style="{ '--stagger-index': staggerIndex }"
  >
    <!-- Emoji placeholder -->
    <div class="w-12 h-12 rounded-full skeleton-shimmer mb-2"></div>

    <!-- Name placeholder -->
    <div class="w-20 h-5 rounded skeleton-shimmer mb-2"></div>

    <!-- Count placeholder -->
    <div class="flex-1 flex items-center justify-center my-2">
      <div class="w-16 h-12 rounded skeleton-shimmer"></div>
    </div>

    <!-- Status badge placeholder -->
    <div class="w-24 h-6 rounded-full skeleton-shimmer"></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  staggerIndex?: number
}>()
</script>
