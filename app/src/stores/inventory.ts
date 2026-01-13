/**
 * Inventory Pinia store.
 */

import { defineStore } from 'pinia'
import type { InventoryItem, InventoryResponse } from '@/types/inventory'

interface InventoryState {
  items: InventoryItem[]
  lastUpdated: Date | null
  loading: boolean
  error: string | null
  machineId: string
  location: string
  // Track previous counts for restock detection
  previousCounts: Map<string, number>
  // Items that just came back in stock
  justRestocked: Set<string>
}

export const useInventoryStore = defineStore('inventory', {
  state: (): InventoryState => ({
    items: [],
    lastUpdated: null,
    loading: false,
    error: null,
    machineId: import.meta.env.VITE_MACHINE_ID || 'breakroom-1',
    location: 'Break Room',
    previousCounts: new Map(),
    justRestocked: new Set()
  }),

  getters: {
    availableItems: (state) => state.items.filter(item => item.count > 0),
    outOfStockItems: (state) => state.items.filter(item => item.count === 0),
    totalItems: (state) => state.items.reduce((sum, item) => sum + item.count, 0)
  },

  actions: {
    async fetchInventory(silent = false) {
      if (!silent) {
        this.loading = true
      }
      this.error = null

      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

        // SQLite backend uses simple /inventory endpoint (no machine_id path)
        const response = await fetch(`${apiUrl}/inventory`)

        if (!response.ok) {
          throw new Error('Failed to fetch inventory')
        }

        const data: InventoryResponse = await response.json()

        // Clear previous restocked set before detecting new restocks
        this.justRestocked.clear()

        // Backend returns items as array, transform to our internal format
        const newItems = data.items.map((item) => ({
          name: item.display_name || item.item_name,
          count: item.count,
          confidence: item.confidence,
          inStock: item.count > 0
        }))

        // Detect restocked items (was 0, now > 0)
        for (const item of newItems) {
          const prevCount = this.previousCounts.get(item.name) ?? -1
          if (prevCount === 0 && item.count > 0) {
            this.justRestocked.add(item.name)
          }
          this.previousCounts.set(item.name, item.count)
        }

        this.items = newItems

        this.machineId = data.device_id
        this.location = data.location
        this.lastUpdated = data.last_updated ? new Date(data.last_updated) : null

      } catch (e) {
        this.error = e instanceof Error ? e.message : 'Unknown error'
      } finally {
        if (!silent) {
          this.loading = false
        }
      }
    }
  }
})
