<template>
  <article
    class="rounded-2xl p-4 min-h-[160px] shadow-card transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5 flex flex-col items-center text-center"
    :class="cardGradientClass"
    :aria-label="`${displayName}: ${ariaLabel}`"
  >
    <!-- Large Centered Emoji -->
    <span class="text-5xl mb-2" aria-hidden="true">{{ emoji }}</span>

    <!-- Snack Name -->
    <h3 class="font-display font-bold text-gray-900 dark:text-gray-100 truncate w-full" :title="item.name">
      {{ displayName }}
    </h3>

    <!-- Prominent Count Display -->
    <div class="flex-1 flex items-center justify-center my-2">
      <template v-if="item.count > 0">
        <span class="text-count-display text-gray-900 dark:text-white">
          {{ item.count }}
        </span>
      </template>
      <template v-else>
        <span class="text-base text-gray-500 dark:text-gray-400 italic">
          Come back soon!
        </span>
      </template>
    </div>

    <!-- Status Badge Component -->
    <StatusBadge :status="statusType" :count="item.count" />
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InventoryItem } from '@/types/inventory'
import StatusBadge, { type StatusType } from './StatusBadge.vue'

const props = defineProps<{
  item: InventoryItem
}>()

// Stock level computation: high (>3), low (1-3), out (0)
const stockLevel = computed(() => {
  if (props.item.count === 0) return 'out'
  if (props.item.count <= 3) return 'low'
  return 'high'
})

// Map stock level to status type
const statusType = computed<StatusType>(() => {
  switch (stockLevel.value) {
    case 'high':
      return 'available'
    case 'low':
      return 'low'
    case 'out':
      return 'out'
    default:
      return 'available'
  }
})

// Card gradient based on stock level
const cardGradientClass = computed(() => {
  switch (stockLevel.value) {
    case 'high':
      return 'bg-card-available'
    case 'low':
      return 'bg-card-warning'
    case 'out':
      return 'bg-card-empty grayscale-[30%]'
    default:
      return 'bg-card-available'
  }
})

// ARIA label for accessibility
const ariaLabel = computed(() => {
  switch (stockLevel.value) {
    case 'high':
      return `${props.item.count} items available`
    case 'low':
      return `Only ${props.item.count} items left`
    case 'out':
      return 'Out of stock'
    default:
      return `${props.item.count} items available`
  }
})

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
