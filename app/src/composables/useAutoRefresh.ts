/**
 * Auto-refresh composable for periodic data fetching.
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useDocumentVisibility } from '@vueuse/core'

export function useAutoRefresh(
  fetchFn: () => Promise<void>,
  intervalMs: number = 30000
) {
  const secondsUntilRefresh = ref(intervalMs / 1000)
  const isRefreshing = ref(false)
  const visibility = useDocumentVisibility()

  let refreshInterval: ReturnType<typeof setInterval> | null = null
  let countdownInterval: ReturnType<typeof setInterval> | null = null

  const refresh = async () => {
    isRefreshing.value = true
    try {
      await fetchFn()
    } finally {
      isRefreshing.value = false
      resetCountdown()
    }
  }

  const resetCountdown = () => {
    secondsUntilRefresh.value = intervalMs / 1000
  }

  const startIntervals = () => {
    stopIntervals()

    // Countdown timer (every second)
    countdownInterval = setInterval(() => {
      if (secondsUntilRefresh.value > 0) {
        secondsUntilRefresh.value--
      }
    }, 1000)

    // Refresh timer
    refreshInterval = setInterval(refresh, intervalMs)
  }

  const stopIntervals = () => {
    if (countdownInterval) {
      clearInterval(countdownInterval)
      countdownInterval = null
    }
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  // Handle tab visibility
  watch(visibility, (isVisible) => {
    if (isVisible === 'visible') {
      refresh()
      startIntervals()
    } else {
      stopIntervals()
    }
  })

  onMounted(() => {
    startIntervals()
  })

  onUnmounted(() => {
    stopIntervals()
  })

  return {
    secondsUntilRefresh,
    isRefreshing,
    refresh,
    resetCountdown
  }
}
