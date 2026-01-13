<template>
  <article
    class="card-enter rounded-2xl p-4 min-h-[160px] shadow-card transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5 flex flex-col items-center text-center"
    :class="[cardGradientClass, { 'low-stock-pulse': stockLevel === 'low' }]"
    :style="{ '--stagger-index': staggerIndex }"
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
        <div class="flex flex-col items-center">
          <span
            class="text-count-display text-gray-900 dark:text-white"
            :class="{ 'count-changed': countAnimating }"
            @animationend="countAnimating = false"
          >
            {{ item.count }}
          </span>
          <!-- Going Fast indicator for low stock -->
          <span v-if="stockLevel === 'low'" class="going-fast">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"/>
            </svg>
            Going fast!
          </span>
        </div>
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
import { computed, ref, watch } from 'vue'
import type { InventoryItem } from '@/types/inventory'
import StatusBadge, { type StatusType } from './StatusBadge.vue'

const props = defineProps<{
  item: InventoryItem
  staggerIndex?: number
}>()

// Count change animation state
const countAnimating = ref(false)
const previousCount = ref(props.item.count)

// Watch for count changes to trigger animation
watch(
  () => props.item.count,
  (newCount, oldCount) => {
    if (oldCount !== undefined && newCount !== oldCount) {
      countAnimating.value = true
      previousCount.value = newCount
    }
  }
)

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
