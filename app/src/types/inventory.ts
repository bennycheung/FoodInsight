/**
 * Inventory data types.
 */

export interface InventoryItem {
  name: string
  count: number
  confidence: number
  inStock: boolean
}

/**
 * API response from /inventory endpoint.
 * SQLite backend returns items as an array.
 */
export interface InventoryResponse {
  device_id: string
  location: string
  items: Array<{
    item_name: string
    display_name: string
    count: number
    confidence: number
    last_updated: string | null
  }>
  last_updated: string | null
}
