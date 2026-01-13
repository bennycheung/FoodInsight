# Epic 4: UX Delight - Animations & Interactions

**Epic Goal:** Add playful animations and enhanced interactions including card entry effects, count change animations, low stock warnings, refresh indicators, and mobile pull-to-refresh.

**PRD Reference:** [[FoodInsight PRD]]
**Architecture Reference:** [[FoodInsight Solution Architecture]]
**UX Reference:** [[FoodInsight UX Specification]]

**Epic Acceptance Criteria:**
- [x] Cards animate in with staggered entry on page load
- [x] Count changes trigger visual pulse animation
- [x] Low stock items have subtle orange pulse effect
- [x] Refresh indicator shows circular countdown progress
- [x] Pull-to-refresh works on mobile devices
- [x] All animations respect `prefers-reduced-motion`

**Prerequisite:** Epic 3 (UX Foundation) must be complete

---

## E4-S1: Card Entry and Count Change Animations

### User Story

**As a** user,
**I want** playful animations when cards load and when counts change,
**So that** the interface feels responsive and delightful, drawing attention to important updates.

### Acceptance Criteria

```gherkin
Feature: Card Animations

Scenario: Cards animate in on page load
  Given I open the app
  When the inventory loads
  Then cards fade in with upward slide
  And each card enters 50ms after the previous (staggered)
  And cards have subtle bounce at end of animation

Scenario: Entry animation has correct timing
  Given cards are animating in
  Then animation duration is 300-500ms
  And easing is ease-out with bounce overshoot
  And total stagger for 8 cards is ~400ms

Scenario: Count changes trigger animation
  Given a card is displayed
  When the count value changes on refresh
  Then the count number scales up briefly (1 → 1.2 → 1)
  And a brief color flash occurs
  And animation duration is 200-300ms

Scenario: Animations respect reduced motion
  Given user has prefers-reduced-motion enabled
  When cards load or counts change
  Then no motion animations play
  And state changes are instant
  And content is still visible

Scenario: Skeleton cards have shimmer
  Given inventory is loading
  When skeleton cards display
  Then they show shimmer animation across surface
```

### Technical Notes

**Entry Animation Keyframes:**
```css
@keyframes cardEnter {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  70% {
    transform: translateY(-5px) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.card-enter {
  animation: cardEnter 400ms ease-out both;
  animation-delay: calc(var(--index) * 50ms);
}
```

**Count Change Animation:**
```css
@keyframes countChange {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); color: var(--snack-purple); }
  100% { transform: scale(1); }
}

.count-changed {
  animation: countChange 250ms ease-in-out;
}
```

**Reduced Motion:**
```css
@media (prefers-reduced-motion: reduce) {
  .card-enter,
  .count-changed {
    animation: none;
  }
}
```

**Stagger Implementation:**
```vue
<SnackCard
  v-for="(item, index) in sortedItems"
  :key="item.name"
  :item="item"
  :style="{ '--index': index }"
/>
```

### Definition of Done

- [x] Card entry animation implemented with stagger
- [x] Bounce overshoot effect working
- [x] Count change animation triggers on value change
- [x] Skeleton shimmer animation added
- [x] `prefers-reduced-motion` disables all animations
- [x] Animation timing matches spec (300-500ms entry, 200-300ms count)

### Visual Testing Checklist

- [ ] Record video of initial page load with staggered card entry
- [ ] Record video of count changing (simulate via dev tools)
- [ ] Verify stagger timing (each card 50ms after previous)
- [ ] Check animation feels "bouncy" not "robotic"
- [ ] Test with `prefers-reduced-motion: reduce` enabled
- [ ] Verify skeleton shimmer animation

### Dependencies

- **Blocked by:** Epic 3 complete
- **Blocks:** E4-S2 (Low Stock Warning)

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - animation timing requires tuning

### Files to Modify

- `app/src/assets/main.css`
- `app/src/components/SnackCard.vue`
- `app/src/components/SkeletonCard.vue`
- `app/src/views/InventoryView.vue`

---

## E4-S2: Low Stock Warning Effects

### User Story

**As a** user,
**I want** low stock items to have a gentle pulsing glow and "going fast!" indicator,
**So that** I know to hurry if I want that snack before it's gone.

### Acceptance Criteria

```gherkin
Feature: Low Stock Warning

Scenario: Low stock cards pulse
  Given a snack has count 1-3
  When the card displays
  Then an orange glow pulse animation plays
  And the pulse expands from 0 to 8px
  And animation cycles every 2-3 seconds

Scenario: Going fast indicator shows
  Given a snack has low stock
  When the card renders
  Then "Going fast!" or lightning indicator is visible
  And it's positioned near the count or corner
  And styled with warning orange color

Scenario: Pulse only on first view
  Given I've already seen a low stock card
  When I return to the page
  Then the pulse should be subtle or limited iterations
  And not distract from other content

Scenario: Reduced motion shows static glow
  Given prefers-reduced-motion is enabled
  And a snack has low stock
  When the card displays
  Then a static orange glow shows (no animation)
  And "Going fast!" indicator still visible
```

### Technical Notes

**Pulse Animation:**
```css
@keyframes lowStockPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(249, 115, 22, 0);
  }
}

.low-stock-pulse {
  animation: lowStockPulse 2.5s ease-in-out infinite;
}

/* Limit to 3 iterations to avoid distraction */
.low-stock-pulse-limited {
  animation: lowStockPulse 2.5s ease-in-out 3;
}
```

**Going Fast Indicator:**
```vue
<div v-if="stockLevel === 'low'" class="going-fast">
  <svg class="w-3 h-3"><!-- lightning --></svg>
  <span>Going fast!</span>
</div>
```

**Reduced Motion Alternative:**
```css
@media (prefers-reduced-motion: reduce) {
  .low-stock-pulse {
    animation: none;
    box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.3);
  }
}
```

### Definition of Done

- [x] Pulse animation implemented for low stock cards
- [x] Animation timing is 2-3 second cycle
- [x] "Going fast!" text/icon indicator added
- [x] Pulse limited to 3 iterations (or subtle infinite)
- [x] Reduced motion shows static glow
- [x] Warning orange color matches spec (#f97316)

### Visual Testing Checklist

- [ ] Screenshot card with low stock pulse at peak glow
- [ ] Record video of pulse animation cycle
- [ ] Verify "going fast!" text is visible and readable
- [ ] Check pulse color matches Warning Orange (#f97316)
- [ ] Test reduced motion mode shows static glow
- [ ] Ensure pulse doesn't distract from other cards

### Dependencies

- **Blocked by:** E4-S1 (Card Animations)
- **Blocks:** None directly

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - contained animation addition

### Files to Modify

- `app/src/components/SnackCard.vue`
- `app/src/assets/main.css`

---

## E4-S3: Enhanced Refresh Indicator

### User Story

**As a** user,
**I want** a playful refresh indicator that shows countdown progress and animated refresh state,
**So that** I know when fresh data is coming and trust that the information is current.

### Acceptance Criteria

```gherkin
Feature: Refresh Indicator

Scenario: Countdown shows circular progress
  Given the auto-refresh timer is running
  When I view the refresh indicator
  Then a circular progress ring shows countdown
  And seconds remaining display in center
  And progress depletes as time passes

Scenario: Refresh animation plays during fetch
  Given I trigger a manual refresh
  When the API call is in progress
  Then the refresh button spins smoothly
  And animation continues until data returns

Scenario: Success shows checkmark flash
  Given a refresh completes successfully
  Then a green checkmark briefly flashes
  And the checkmark fades after ~500ms
  And countdown resets to 30 seconds

Scenario: Error shows shake and retry
  Given a refresh fails
  Then the indicator shakes briefly
  And shows red color
  And "Retry" option is visible

Scenario: Last updated shows friendly time
  Given data was last fetched
  When I view last updated text
  Then it shows "just now" for <10 seconds
  Or "X seconds ago" for <60 seconds
  Or "X minutes ago" for older
```

### Technical Notes

**Circular Progress SVG:**
```vue
<svg class="w-8 h-8" viewBox="0 0 36 36">
  <!-- Background circle -->
  <circle cx="18" cy="18" r="16" fill="none"
    stroke="#e5e7eb" stroke-width="3"/>
  <!-- Progress circle -->
  <circle cx="18" cy="18" r="16" fill="none"
    stroke="#8b5cf6" stroke-width="3"
    :stroke-dasharray="circumference"
    :stroke-dashoffset="progressOffset"
    transform="rotate(-90 18 18)"/>
  <!-- Center text -->
  <text x="18" y="21" text-anchor="middle"
    class="text-xs font-bold">{{ seconds }}</text>
</svg>
```

**Progress Calculation:**
```typescript
const circumference = 2 * Math.PI * 16 // ~100.5
const progressOffset = computed(() =>
  circumference * (1 - secondsRemaining.value / 30)
)
```

**Refresh Spin Animation:**
```css
@keyframes refreshSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.refreshing {
  animation: refreshSpin 1s linear infinite;
}
```

**Friendly Time Formatting:**
```typescript
function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 10) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}m ago`
}
```

### Definition of Done

- [x] Circular progress indicator created
- [x] Seconds display in center of ring
- [x] Spin animation during refresh
- [x] Success checkmark flash implemented
- [x] Error shake animation implemented
- [x] "Last updated" shows friendly relative time
- [x] RefreshIndicator component extracted

### Visual Testing Checklist

- [ ] Screenshot countdown at various states (30s, 15s, 5s)
- [ ] Record video of refresh button spin animation
- [ ] Screenshot success checkmark flash
- [ ] Screenshot error shake state
- [ ] Verify "last updated" formatting is friendly

### Dependencies

- **Blocked by:** E3-S1 (Design Tokens for colors)
- **Blocks:** E4-S4 (Pull-to-Refresh)

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - SVG progress requires precision

### Files to Modify

- `app/src/components/RefreshIndicator.vue` (new)
- `app/src/components/LastUpdated.vue`
- `app/src/views/InventoryView.vue`
- `app/src/assets/main.css`

---

## E4-S4: Mobile Pull-to-Refresh

### User Story

**As a** mobile user,
**I want** to pull down on the screen to trigger a refresh,
**So that** I can quickly check for updates using a familiar mobile gesture.

### Acceptance Criteria

```gherkin
Feature: Pull-to-Refresh

Scenario: Pull gesture triggers refresh on mobile
  Given I'm on a touch device
  When I pull down from top of content (>60px)
  Then a refresh is triggered
  And the refresh indicator appears
  And data reloads from API

Scenario: Visual feedback during pull
  Given I'm pulling down
  When pull distance is 20-60px
  Then a refresh icon appears proportionally
  And icon scales with pull distance
  When I release before threshold
  Then gesture cancels and snaps back

Scenario: Haptic feedback on trigger
  Given I'm on a device with haptic support
  When pull exceeds threshold and triggers
  Then device vibrates briefly
  And provides tactile confirmation

Scenario: Pull disabled on desktop
  Given I'm using mouse input
  When I try to pull/scroll down
  Then no pull-to-refresh behavior occurs
  And normal scrolling works

Scenario: Integrates with auto-refresh
  Given I manually pull to refresh
  When refresh completes
  Then the auto-refresh countdown resets to 30s
```

### Technical Notes

**Touch Event Handling:**
```typescript
const usePullToRefresh = (onRefresh: () => Promise<void>) => {
  const startY = ref(0)
  const pullDistance = ref(0)
  const isPulling = ref(false)
  const threshold = 60

  const onTouchStart = (e: TouchEvent) => {
    if (window.scrollY === 0) {
      startY.value = e.touches[0].clientY
      isPulling.value = true
    }
  }

  const onTouchMove = (e: TouchEvent) => {
    if (!isPulling.value) return
    pullDistance.value = Math.max(0, e.touches[0].clientY - startY.value)
  }

  const onTouchEnd = async () => {
    if (pullDistance.value >= threshold) {
      await onRefresh()
      triggerHaptic()
    }
    pullDistance.value = 0
    isPulling.value = false
  }

  return { pullDistance, isPulling, onTouchStart, onTouchMove, onTouchEnd }
}
```

**Haptic Feedback:**
```typescript
function triggerHaptic() {
  if ('vibrate' in navigator) {
    navigator.vibrate(10)
  }
}
```

**CSS for Pull Indicator:**
```css
.pull-indicator {
  position: absolute;
  top: -50px;
  left: 50%;
  transform: translateX(-50%) translateY(var(--pull-offset));
  transition: transform 0.1s ease-out;
}

/* Prevent pull-to-refresh interference */
html {
  overscroll-behavior-y: contain;
}
```

**Desktop Detection:**
```typescript
const isTouchDevice = 'ontouchstart' in window ||
  navigator.maxTouchPoints > 0
```

### Definition of Done

- [x] Pull gesture detected on touch devices
- [x] Pull indicator appears during drag
- [x] Threshold (60px) triggers refresh
- [x] Haptic feedback on supported devices
- [x] Desktop mouse users not affected
- [x] Auto-refresh timer resets after manual pull
- [x] Overscroll behavior handled

### Visual Testing Checklist

- [ ] Test on iOS Safari (pull down gesture)
- [ ] Test on Android Chrome (pull down gesture)
- [ ] Verify pull indicator appears smoothly
- [ ] Check haptic feedback triggers on iOS
- [ ] Confirm desktop mouse scroll doesn't trigger
- [ ] Test integration with auto-refresh timer

### Dependencies

- **Blocked by:** E4-S3 (Refresh Indicator)
- **Blocks:** None

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - touch events tricky across browsers

### Files to Modify

- `app/src/composables/usePullToRefresh.ts` (new)
- `app/src/views/InventoryView.vue`
- `app/src/App.vue`

---

## Epic 4 Summary

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| E4-S1 | Card Animations | 5 | Epic 3 |
| E4-S2 | Low Stock Warning | 3 | E4-S1 |
| E4-S3 | Refresh Indicator | 5 | E3-S1 |
| E4-S4 | Pull-to-Refresh | 5 | E4-S3 |
| **Total** | | **18** | |

**Dependency Graph:**
```
Epic 3 Complete
    │
    ├──► E4-S1 Card Animations
    │         │
    │         └──► E4-S2 Low Stock Warning
    │
    └──► E4-S3 Refresh Indicator
              │
              └──► E4-S4 Pull-to-Refresh
```

**Milestone Checkpoint:** After Epic 4 completion, all animations from UX spec section 8 should be implemented and respect `prefers-reduced-motion`. Test on real mobile devices.
