/**
 * Inventory data types.
 */

export interface InventoryItem {
  name: string
  count: number
  confidence: number
  inStock: boolean
}

export interface InventoryResponse {
  machine_id: string
  location: string
  items: Record<string, { count: number; confidence: number }>
  last_updated: string | null
}
