<template>
  <div
    class="rounded-lg p-4 shadow-sm transition-all"
    :class="cardClasses"
  >
    <div class="flex items-center justify-between mb-2">
      <span class="text-2xl">{{ emoji }}</span>
      <span
        class="px-2 py-1 text-xs rounded-full"
        :class="statusClasses"
      >
        {{ statusText }}
      </span>
    </div>

    <h3 class="font-medium text-gray-900 truncate" :title="item.name">
      {{ displayName }}
    </h3>

    <div class="mt-2">
      <span v-if="item.inStock" class="text-3xl font-bold text-gray-900">
        {{ item.count }}
      </span>
      <span v-else class="text-lg text-gray-400">
        Out of Stock
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InventoryItem } from '@/types/inventory'

const props = defineProps<{
  item: InventoryItem
}>()

const cardClasses = computed(() => ({
  'bg-white': props.item.inStock,
  'bg-gray-100 opacity-60': !props.item.inStock
}))

const statusClasses = computed(() => ({
  'bg-green-100 text-green-800': props.item.inStock,
  'bg-gray-200 text-gray-600': !props.item.inStock
}))

const statusText = computed(() =>
  props.item.inStock ? 'Available' : 'Empty'
)

// Map item names to emojis
const emojiMap: Record<string, string> = {
  chips_bag: '🥔',
  candy_bar: '🍫',
  granola_bar: '🥜',
  soda_can: '🥤',
  water_bottle: '💧',
  energy_drink: '⚡',
  cookies_pack: '🍪',
  nuts_pack: '🥜',
  apple: '🍎',
  banana: '🍌',
  orange: '🍊',
  default: '🍿'
}

const emoji = computed(() =>
  emojiMap[props.item.name] || emojiMap.default
)

const displayName = computed(() =>
  props.item.name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
)
</script>
