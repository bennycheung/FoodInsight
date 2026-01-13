# Epic 5: UX Polish - Final Touches & Accessibility

**Epic Goal:** Complete the UX refresh with dark mode support, celebration effects, comprehensive accessibility audit, responsive grid refinement, and enhanced offline experience.

**PRD Reference:** [[FoodInsight PRD]]
**Architecture Reference:** [[FoodInsight Solution Architecture]]
**UX Reference:** [[FoodInsight UX Specification]]

**Epic Acceptance Criteria:**
- [x] Dark mode automatically activates based on system preference
- [x] Back-in-stock items trigger celebration animation
- [x] Lighthouse accessibility score reaches 100
- [x] Grid adapts optimally across all breakpoints
- [x] Offline banner matches playful design with smooth animations

**Prerequisite:** Epic 3 (UX Foundation) must be complete; Epic 4 for celebration effects

---

## E5-S1: Dark Mode Support

### User Story

**As a** user,
**I want** the app to support dark mode based on my system preference,
**So that** the app is comfortable to use in low-light environments and matches my device theme.

### Acceptance Criteria

```gherkin
Feature: Dark Mode Support

Scenario: App detects system dark mode preference
  Given my system has dark mode enabled
  When I open the app
  Then the app automatically displays in dark mode
  And no manual toggle is needed

Scenario: Background colors adapt to dark mode
  Given dark mode is active
  When the app displays
  Then page background is #1a1625 (dark purple)
  And card backgrounds are #2d2640
  And surfaces have appropriate depth

Scenario: Text colors maintain readability
  Given dark mode is active
  When I view text content
  Then primary text is #f9fafb (near white)
  And secondary text is #9ca3af (muted gray)
  And all text meets WCAG contrast requirements

Scenario: Header gradient remains vibrant
  Given dark mode is active
  When the header displays
  Then the purple-to-pink gradient remains vibrant
  And looks good against dark background

Scenario: Status badges maintain readability
  Given dark mode is active
  When I view stock status badges
  Then all badge colors are distinguishable
  And text contrast meets 4.5:1 ratio

Scenario: Smooth transition on theme change
  Given I toggle system theme
  When dark mode activates or deactivates
  Then colors transition smoothly (~200ms)
  And there is no flash of unstyled content
```

### Technical Notes

**Dark Mode Color Mapping:**
| Purpose | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | #faf5ff | #1a1625 |
| Card Background | #ffffff | #2d2640 |
| Text Primary | #1f2937 | #f9fafb |
| Text Secondary | #6b7280 | #9ca3af |

**Tailwind v4 Dark Mode Setup:**
```css
@theme {
  --color-bg-dark: #1a1625;
  --color-card-dark: #2d2640;
}

/* Apply with media query */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: var(--color-bg-dark);
    --color-card: var(--color-card-dark);
  }
}
```

**Smooth Transition:**
```css
body {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out;
}

.card {
  transition: background-color 200ms ease-in-out;
}
```

### Definition of Done

- [x] App detects system dark mode preference
- [x] Background changes to #1a1625 in dark mode
- [x] Card backgrounds change to #2d2640
- [x] Text colors adjust correctly (primary/secondary)
- [x] Header gradient looks good on dark background
- [x] Status badges remain readable
- [x] All contrasts meet WCAG 4.5:1
- [x] Smooth transition on theme change

### Visual Testing Checklist

- [ ] Screenshot full app in light mode
- [ ] Screenshot full app in dark mode
- [ ] Verify header gradient on dark background
- [ ] Check card gradients adapt appropriately
- [ ] Test contrast ratios with browser dev tools
- [ ] Toggle system dark mode and verify smooth transition
- [ ] Test on iOS and macOS dark mode

### Dependencies

- **Blocked by:** E3-S1 (Design Tokens)
- **Blocks:** None

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - requires thorough testing across all components

### Files to Modify

- `app/src/assets/main.css`
- `app/src/App.vue`
- `app/src/components/SnackCard.vue`
- `app/src/components/StatusBadge.vue`

---

## E5-S2: Back-in-Stock Celebration Effects

### User Story

**As a** user,
**I want** a celebration animation when an item comes back in stock,
**So that** I feel excited about the restocked item and notice the positive change immediately.

### Acceptance Criteria

```gherkin
Feature: Celebration Effects

Scenario: Restocked item shows celebration
  Given a snack was previously out of stock (count 0)
  When it comes back in stock (count > 0) after refresh
  Then a celebration animation plays on the card
  And confetti or sparkle effect bursts around the card

Scenario: "Back in stock" badge displays
  Given an item just came back in stock
  When the card renders
  Then a "Back in stock!" badge appears
  And badge has blue gradient (#3b82f6 to #2563eb)
  And a star icon is visible in the badge

Scenario: Animation has correct timing
  Given a celebration animation triggers
  Then animation duration is 600-800ms
  And uses spring/bounce easing
  And animation elements clean up after completion

Scenario: Celebration triggers only once per restock
  Given an item came back in stock
  And celebration has already played
  When I refresh the page again
  Then no new celebration animation plays
  And badge may still show "Back in stock!" for a period

Scenario: Reduced motion shows static badge
  Given prefers-reduced-motion is enabled
  And an item comes back in stock
  When the card displays
  Then "Back in stock!" badge shows
  But no animation or confetti plays
```

### Technical Notes

**Restock Detection Logic:**
```typescript
// In inventory store
const previousCounts = ref<Map<string, number>>(new Map())
const justRestocked = ref<Set<string>>(new Set())

function detectRestocks(newItems: InventoryItem[]) {
  justRestocked.value.clear()
  for (const item of newItems) {
    const prevCount = previousCounts.value.get(item.name) ?? 0
    if (prevCount === 0 && item.count > 0) {
      justRestocked.value.add(item.name)
    }
    previousCounts.value.set(item.name, item.count)
  }
}
```

**Celebration Animation:**
```css
@keyframes celebrate {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 20px 10px rgba(59, 130, 246, 0.2);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

.card-celebrate {
  animation: celebrate 800ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
```

**Confetti Options:**
- CSS-only pseudo-element approach
- Lightweight canvas-confetti library (~3KB)
- Custom Vue component with particles

### Definition of Done

- [x] Restock detection logic implemented
- [x] Celebration animation triggers on restock
- [x] "Back in stock!" badge with blue gradient
- [x] Star icon in restocked badge
- [x] Animation uses spring easing (600-800ms)
- [x] Celebration only triggers once per restock event
- [x] Reduced motion shows static badge only

### Visual Testing Checklist

- [ ] Record video of item going from 0 to >0 count
- [ ] Verify confetti/sparkle animation plays
- [ ] Screenshot "Back in stock!" badge
- [ ] Check badge colors match spec (blue gradient)
- [ ] Test that animation only plays once per restock
- [ ] Verify reduced motion shows static badge

### Dependencies

- **Blocked by:** E4-S1 (Card Animations)
- **Blocks:** None

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - state tracking across refreshes

### Files to Modify

- `app/src/stores/inventory.ts`
- `app/src/components/SnackCard.vue`
- `app/src/components/StatusBadge.vue`
- `app/src/assets/main.css`

---

## E5-S3: WCAG 2.1 AA Accessibility Audit

### User Story

**As a** user with accessibility needs,
**I want** the app to meet WCAG 2.1 Level AA standards,
**So that** I can use the app effectively regardless of visual, motor, or cognitive abilities.

### Acceptance Criteria

```gherkin
Feature: Accessibility Compliance

Scenario: Color contrast meets requirements
  Given any text element in the app
  When I check its contrast ratio
  Then normal text has at least 4.5:1 contrast
  And large text (18px+/bold 14px+) has at least 3:1 contrast

Scenario: Status not conveyed by color alone
  Given any stock status indicator
  When it displays
  Then it shows color AND icon AND text
  And status is understandable without seeing colors

Scenario: Focus indicators are visible
  Given I'm navigating with keyboard
  When I tab through interactive elements
  Then each element shows a visible focus ring
  And focus ring has sufficient contrast

Scenario: Screen reader announces correctly
  Given I'm using a screen reader (VoiceOver/NVDA)
  When I navigate through snack cards
  Then stock status is announced clearly
  And ARIA labels provide full context
  And announcement includes count and status

Scenario: Touch targets are adequate
  Given any interactive element
  When I measure its tap area
  Then minimum dimension is 44x44px
  And there is adequate spacing between targets

Scenario: Animations respect user preferences
  Given prefers-reduced-motion is enabled
  When the app displays animations
  Then no motion animations play
  And state changes are instant
  And content remains visible

Scenario: Semantic HTML is used
  Given the HTML structure
  When I inspect the DOM
  Then proper landmarks are used (header, main, article)
  And heading hierarchy is logical (h1, h2, etc.)
  And lists use proper list elements
```

### Technical Notes

**ARIA Labels:**
| Status | ARIA Label |
|--------|------------|
| In Stock (High) | "{count} items available" |
| Low Stock | "Only {count} items left" |
| Out of Stock | "Out of stock" |
| Just Restocked | "Back in stock! {count} available" |

**Focus Ring Styling:**
```css
/* Visible focus ring with brand color */
:focus-visible {
  outline: 2px solid var(--snack-purple);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Remove default focus for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}
```

**Touch Target Padding:**
```css
.interactive-element {
  min-width: 44px;
  min-height: 44px;
  padding: 12px;
}
```

**Semantic Structure:**
```html
<header><!-- App header --></header>
<main>
  <h1 class="sr-only">Snack Inventory</h1>
  <section aria-labelledby="snacks-heading">
    <h2 id="snacks-heading" class="sr-only">Available Snacks</h2>
    <article role="listitem" aria-label="Chips: 5 items available">
      <!-- SnackCard -->
    </article>
  </section>
</main>
```

### Definition of Done

- [x] All text meets 4.5:1 contrast ratio
- [x] Status uses color + icon + text (not color alone)
- [x] All interactive elements have visible focus indicators
- [x] Screen reader announces status correctly (ARIA labels)
- [x] Touch targets minimum 44x44px
- [x] All animations respect `prefers-reduced-motion`
- [x] Page uses semantic HTML with proper landmarks
- [x] Lighthouse accessibility score: 100
- [x] aXe DevTools: zero violations

### Visual Testing Checklist

- [ ] Run Lighthouse accessibility audit (target 100)
- [ ] Run aXe DevTools scan (zero violations)
- [ ] Test full app flow with VoiceOver (macOS/iOS)
- [ ] Test full app flow with keyboard only (Tab navigation)
- [ ] Verify all focus states are visible
- [ ] Check touch target sizes on mobile
- [ ] Test with `prefers-reduced-motion: reduce`

### Dependencies

- **Blocked by:** Epic 4 complete (all animations implemented)
- **Blocks:** None (final validation story)

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Low - audit and fix existing components

### Files to Modify

- `app/src/App.vue`
- `app/src/components/SnackCard.vue`
- `app/src/components/StatusBadge.vue`
- `app/src/views/InventoryView.vue`
- `app/src/assets/main.css`

---

## E5-S4: Responsive Grid Refinement

### User Story

**As a** user on any device,
**I want** the snack grid to adapt perfectly to my screen size,
**So that** I get the optimal viewing experience whether on phone, tablet, or desktop.

### Acceptance Criteria

```gherkin
Feature: Responsive Grid

Scenario: Mobile layout (< 640px)
  Given I'm viewing on a mobile device
  When the grid displays
  Then cards are arranged in 2 columns
  And gap between cards is 12px
  And content is full-width with small margins

Scenario: Tablet layout (640px - 1024px)
  Given I'm viewing on a tablet
  When the grid displays
  Then cards are arranged in 3 columns
  And gap between cards is 16px
  And content has moderate side margins

Scenario: Desktop layout (> 1024px)
  Given I'm viewing on a desktop
  When the grid displays
  Then cards are arranged in 4 columns
  And gap between cards is 20px
  And content has max-width container centered

Scenario: Large desktop respects max width
  Given I'm viewing on a large monitor (> 1440px)
  When the grid displays
  Then content width is capped (max-w-6xl)
  And content remains centered
  And grid doesn't stretch too wide

Scenario: Cards maintain consistency
  Given any screen size
  When cards display
  Then all cards have consistent min-height
  And aspect ratio is maintained
  And content doesn't overflow

Scenario: Grid transitions smoothly
  Given I'm resizing the browser window
  When columns change breakpoints
  Then reflow happens smoothly
  And there's no jarring content jump
```

### Technical Notes

**Grid System from UX Spec:**
| Breakpoint | Columns | Gap | Container |
|------------|---------|-----|-----------|
| Mobile (<640px) | 2 | 12px (gap-3) | Full width |
| Tablet (640-1024px) | 3 | 16px (gap-4) | Moderate margins |
| Desktop (>1024px) | 4 | 20px (gap-5) | max-w-6xl centered |

**Tailwind Classes:**
```html
<div class="grid grid-cols-2 gap-3
            sm:grid-cols-3 sm:gap-4
            lg:grid-cols-4 lg:gap-5">
```

**Container Constraints:**
```html
<main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
```

**Card Min-Height:**
```css
.snack-card {
  min-height: 160px;
}
```

### Definition of Done

- [x] Mobile: 2 columns with 12px gap
- [x] Tablet: 3 columns with 16px gap
- [x] Desktop: 4 columns with 20px gap
- [x] Container max-width on large screens
- [x] Content centered at all breakpoints
- [x] Cards maintain min-height consistency
- [x] Grid transitions smoothly on resize

### Visual Testing Checklist

- [ ] Screenshot at 375px width (mobile - 2 columns)
- [ ] Screenshot at 768px width (tablet - 3 columns)
- [ ] Screenshot at 1280px width (desktop - 4 columns)
- [ ] Screenshot at 1920px width (large desktop - max width)
- [ ] Resize browser and verify smooth transitions
- [ ] Verify gap sizes match spec at each breakpoint
- [ ] Check cards maintain consistent height

### Dependencies

- **Blocked by:** E3-S3 (SnackCard Redesign)
- **Blocks:** None

### Complexity

**Points:** 2 (Small)
**Risk:** Low - CSS adjustments only

### Files to Modify

- `app/src/views/InventoryView.vue`
- `app/src/App.vue`

---

## E5-S5: Enhanced Offline Banner

### User Story

**As a** user with intermittent connectivity,
**I want** a friendly, themed offline banner that matches the playful design,
**So that** I understand the app is offline but still trust the cached data I'm seeing.

### Acceptance Criteria

```gherkin
Feature: Offline Banner

Scenario: Offline banner displays when offline
  Given I lose internet connectivity
  When the app detects offline status
  Then a banner appears at top of screen
  And shows friendly offline message

Scenario: Banner matches playful design
  Given the offline banner displays
  Then background is warm yellow (#fef3c7)
  And a cloud-offline icon appears
  And message reads "You're offline - showing last known snacks"
  And optional subtle pattern overlay adds visual interest

Scenario: Banner animates smoothly
  Given I go offline
  When the banner appears
  Then it slides in from top (200-300ms)
  When I come back online
  Then it slides out smoothly
  And disappears completely

Scenario: Refresh button indicates disabled state
  Given I'm offline
  When I view the refresh button
  Then it appears grayed out / disabled
  And tooltip or text explains why
  And clicking it does nothing

Scenario: Banner auto-dismisses on reconnection
  Given the offline banner is showing
  When connectivity is restored
  Then banner slides out automatically
  And refresh button becomes active
  And data may auto-refresh
```

### Technical Notes

**Offline Banner Design:**
```vue
<Transition name="slide-down">
  <div v-if="!isOnline" class="offline-banner">
    <CloudOffIcon class="w-5 h-5" />
    <span>You're offline - showing last known snacks</span>
  </div>
</Transition>
```

**Banner Styling:**
```css
.offline-banner {
  background: linear-gradient(145deg, #fef3c7 0%, #fde68a 100%);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #92400e;
}
```

**Slide Animation:**
```css
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 250ms ease-out, opacity 250ms ease-out;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
```

**Connectivity Detection:**
```typescript
const isOnline = ref(navigator.onLine)

onMounted(() => {
  window.addEventListener('online', () => isOnline.value = true)
  window.addEventListener('offline', () => isOnline.value = false)
})
```

### Definition of Done

- [x] Offline banner has warm yellow background (#fef3c7)
- [x] Cloud-offline icon displayed
- [x] Friendly message: "You're offline - showing last known snacks"
- [x] Banner smoothly animates in/out
- [x] Refresh button disabled (visually indicated) when offline
- [x] Banner auto-dismisses when connection restored
- [x] Matches overall playful design theme

### Visual Testing Checklist

- [ ] Screenshot offline banner appearance
- [ ] Verify yellow background color matches #fef3c7
- [ ] Check icon renders correctly
- [ ] Test message text is readable
- [ ] Toggle airplane mode and verify banner appears/disappears
- [ ] Confirm refresh button shows disabled state
- [ ] Record video of banner animation

### Dependencies

- **Blocked by:** E3-S1 (Design Tokens)
- **Blocks:** None

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - enhancing existing component

### Files to Modify

- `app/src/components/OfflineIndicator.vue`
- `app/src/views/InventoryView.vue`
- `app/src/assets/main.css`

---

## Epic 5 Summary

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| E5-S1 | Dark Mode Support | 5 | E3-S1 |
| E5-S2 | Celebration Effects | 5 | E4-S1 |
| E5-S3 | Accessibility Audit | 5 | Epic 4 |
| E5-S4 | Responsive Grid | 2 | E3-S3 |
| E5-S5 | Offline Banner | 3 | E3-S1 |
| **Total** | | **20** | |

**Dependency Graph:**
```
Epic 3 Complete (Design Tokens)
    │
    ├──► E5-S1 Dark Mode Support
    │
    ├──► E5-S5 Offline Banner
    │
    └──► E5-S4 Responsive Grid (via E3-S3)

Epic 4 Complete (Animations)
    │
    ├──► E5-S2 Celebration Effects (via E4-S1)
    │
    └──► E5-S3 Accessibility Audit

Execution Order (can parallelize):
├── E5-S1, E5-S4, E5-S5 (after Epic 3)
├── E5-S2 (after E4-S1)
└── E5-S3 (after Epic 4 - final validation)
```

**Milestone Checkpoint:** After Epic 5 completion, Lighthouse accessibility score should be 100 and all WCAG 2.1 AA requirements should be met. Dark mode should work seamlessly across all components.
