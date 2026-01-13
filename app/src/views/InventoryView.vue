<template>
  <div>
    <!-- Pull-to-Refresh Indicator (mobile only) -->
    <div
      v-if="isTouchDevice && pullDistance > 0"
      class="pull-indicator"
      :style="{ transform: `translateX(-50%) translateY(${Math.min(pullDistance - 20, 60)}px)` }"
    >
      <div
        class="pull-indicator-icon"
        :class="{ 'refresh-spinning': pullIsRefreshing }"
        :style="{ transform: `rotate(${pullProgress() * 360}deg)` }"
      >
        <svg
          class="w-5 h-5"
          :class="isThresholdMet() ? 'text-snack-purple' : 'text-gray-400'"
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
      </div>
    </div>

    <!-- Header with refresh status -->
    <div class="flex items-center justify-between mb-4">
      <div class="text-sm text-gray-500 dark:text-gray-400">
        <LastUpdated :timestamp="store.lastUpdated" />
      </div>

      <RefreshIndicator
        :seconds="secondsUntilRefresh"
        :total-seconds="30"
        :is-refreshing="isRefreshing"
        :error="!!store.error"
        @refresh="refresh"
      />
    </div>

    <!-- Loading State (only for initial load) -->
    <div v-if="store.loading && store.items.length === 0" class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <SkeletonCard v-for="i in 6" :key="i" :stagger-index="i - 1" />
    </div>

    <!-- Error State -->
    <div v-else-if="store.error && store.items.length === 0" class="text-center py-8">
      <p class="text-red-600 mb-4">{{ store.error }}</p>
      <button
        @click="refresh"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Retry
      </button>
    </div>

    <!-- Inventory Grid -->
    <section v-else aria-labelledby="available-snacks-heading">
      <h3 id="available-snacks-heading" class="sr-only">Available Snacks</h3>

      <!-- Error banner for refresh failures -->
      <div v-if="store.error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-sm" role="alert">
        Update failed. Will retry automatically.
      </div>

      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4 lg:gap-5" role="list">
        <SnackCard
          v-for="(item, index) in sortedItems"
          :key="item.name"
          :item="item"
          :stagger-index="index"
        />
      </div>

      <p v-if="store.items.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        No snacks configured for this location.
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import SnackCard from '@/components/SnackCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import LastUpdated from '@/components/LastUpdated.vue'
import RefreshIndicator from '@/components/RefreshIndicator.vue'

const store = useInventoryStore()

const { secondsUntilRefresh, isRefreshing, refresh } = useAutoRefresh(
  () => store.fetchInventory(true), // Silent refresh
  30000 // 30 seconds
)

// Pull-to-refresh for mobile
const {
  pullDistance,
  isTouchDevice,
  isRefreshing: pullIsRefreshing,
  pullProgress,
  isThresholdMet
} = usePullToRefresh(refresh)

// Sort: available items first, then out of stock
const sortedItems = computed(() => {
  return [...store.items].sort((a, b) => {
    if (a.inStock && !b.inStock) return -1
    if (!a.inStock && b.inStock) return 1
    return a.name.localeCompare(b.name)
  })
})

onMounted(() => {
  store.fetchInventory()
})
</script>
