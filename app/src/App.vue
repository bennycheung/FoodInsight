<template>
  <div class="min-h-screen bg-gray-100 pb-12">
    <header class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-4">
        <h1 class="text-2xl font-bold text-gray-900">FoodInsight</h1>
        <p class="text-sm text-gray-500">{{ location }}</p>
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
