<template>
  <div class="min-h-screen pb-12 font-body">
    <!-- Skip to main content link for keyboard users -->
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <!-- Gradient Header -->
    <header class="bg-header-gradient" role="banner">
      <!-- Mobile: full-width, Desktop: rounded with margin -->
      <div class="max-w-4xl mx-auto px-4 py-4 sm:py-5 sm:mt-4 sm:mx-4 lg:mx-auto sm:rounded-2xl">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4">
          <h1 class="text-app-title text-white drop-shadow-sm">
            <span aria-hidden="true">🍿</span> FoodInsight
          </h1>
          <p class="text-sm sm:text-base text-white/80 font-medium">
            <span aria-hidden="true">📍</span> {{ location }}
          </p>
        </div>
      </div>
    </header>

    <main id="main-content" class="max-w-4xl mx-auto px-4 py-6" role="main">
      <h2 class="sr-only">Snack Inventory</h2>
      <InventoryView />
    </main>

    <OfflineIndicator />
    <PWAUpdatePrompt />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import InventoryView from './views/InventoryView.vue'
import OfflineIndicator from './components/OfflineIndicator.vue'
import PWAUpdatePrompt from './components/PWAUpdatePrompt.vue'

const store = useInventoryStore()
const location = computed(() => store.location || 'Break Room Snacks')
</script>
