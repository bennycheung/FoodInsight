<template>
  <div class="min-h-screen bg-gray-100 dark:bg-bg-dark pb-12 font-body">
    <!-- Gradient Header -->
    <header class="bg-header-gradient">
      <!-- Mobile: full-width, Desktop: rounded with margin -->
      <div class="max-w-4xl mx-auto px-4 py-4 sm:py-5 sm:mt-4 sm:mx-4 lg:mx-auto sm:rounded-2xl">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4">
          <h1 class="text-app-title text-white drop-shadow-sm">
            🍿 FoodInsight
          </h1>
          <p class="text-sm sm:text-base text-white/80 font-medium">
            📍 {{ location }}
          </p>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-6">
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
