/**
 * Pull-to-refresh composable for mobile touch devices.
 * E4-S4: Mobile Pull-to-Refresh
 */

import { ref, onMounted, onUnmounted } from 'vue'

export interface PullToRefreshOptions {
  threshold?: number
  maxPull?: number
}

export function usePullToRefresh(
  onRefresh: () => Promise<void>,
  options: PullToRefreshOptions = {}
) {
  const { threshold = 60, maxPull = 120 } = options

  const startY = ref(0)
  const pullDistance = ref(0)
  const isPulling = ref(false)
  const isRefreshing = ref(false)

  // Check if device supports touch
  const isTouchDevice = ref(false)

  const triggerHaptic = () => {
    if ('vibrate' in navigator) {
      navigator.vibrate(10)
    }
  }

  const onTouchStart = (e: TouchEvent) => {
    // Only start pull if at top of page
    if (window.scrollY === 0 && !isRefreshing.value && e.touches[0]) {
      startY.value = e.touches[0].clientY
      isPulling.value = true
    }
  }

  const onTouchMove = (e: TouchEvent) => {
    if (!isPulling.value || isRefreshing.value || !e.touches[0]) return

    const currentY = e.touches[0].clientY
    const diff = currentY - startY.value

    // Only pull down, not up
    if (diff > 0) {
      // Apply resistance as pull increases (diminishing returns)
      const resistance = 1 - Math.min(diff / maxPull, 1) * 0.5
      pullDistance.value = Math.min(diff * resistance, maxPull)

      // Prevent default scroll when pulling
      if (pullDistance.value > 0) {
        e.preventDefault()
      }
    } else {
      pullDistance.value = 0
    }
  }

  const onTouchEnd = async () => {
    if (!isPulling.value) return

    isPulling.value = false

    if (pullDistance.value >= threshold) {
      // Trigger refresh
      triggerHaptic()
      isRefreshing.value = true

      try {
        await onRefresh()
      } finally {
        isRefreshing.value = false
      }
    }

    // Reset pull distance
    pullDistance.value = 0
  }

  // Calculate progress (0-1) based on threshold
  const pullProgress = () => {
    return Math.min(pullDistance.value / threshold, 1)
  }

  // Check if threshold is met
  const isThresholdMet = () => {
    return pullDistance.value >= threshold
  }

  onMounted(() => {
    // Check for touch support
    isTouchDevice.value = 'ontouchstart' in window || navigator.maxTouchPoints > 0

    if (isTouchDevice.value) {
      // Use passive: false to allow preventDefault on touchmove
      document.addEventListener('touchstart', onTouchStart, { passive: true })
      document.addEventListener('touchmove', onTouchMove, { passive: false })
      document.addEventListener('touchend', onTouchEnd, { passive: true })
    }
  })

  onUnmounted(() => {
    if (isTouchDevice.value) {
      document.removeEventListener('touchstart', onTouchStart)
      document.removeEventListener('touchmove', onTouchMove)
      document.removeEventListener('touchend', onTouchEnd)
    }
  })

  return {
    pullDistance,
    isPulling,
    isRefreshing,
    isTouchDevice,
    pullProgress,
    isThresholdMet
  }
}
