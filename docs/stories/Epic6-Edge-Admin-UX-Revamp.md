# Epic 6: Edge Admin Dashboard UX Revamp

**Epic Goal:** Transform the Edge Admin dashboard from a functional-but-basic Flask+HTMX interface into a visually cohesive experience that matches the "Playful & Vibrant" design language of the consumer PWA.

**PRD Reference:** [[FoodInsight PRD]]
**Architecture Reference:** [[FoodInsight Solution Architecture]]
**UX Reference:** [[FoodInsight UX Specification]]

**Epic Acceptance Criteria:**
- [ ] Admin dashboard uses the same color palette as consumer PWA (Snack Purple, Candy Pink gradients)
- [ ] Dashboard components follow the playful design tokens (rounded corners, shadows, typography)
- [ ] Dark mode support matches consumer PWA implementation
- [ ] Camera preview and ROI configuration UI are visually polished
- [ ] Status indicators use consistent color + icon + text patterns
- [ ] Responsive layout works across desktop, tablet, and mobile viewports
- [ ] All admin UI meets WCAG 2.1 AA accessibility standards

**Prerequisite:** Epic 1 (Edge Detection System) must be complete; Epic 3-5 (UX Foundation/Delight/Polish) for design token reference

---

## E6-S1: Design Token Integration for Admin Portal

### User Story

**As a** system administrator,
**I want** the admin dashboard to use the same visual design language as the consumer app,
**So that** the entire FoodInsight system feels cohesive and professionally designed.

### Acceptance Criteria

```gherkin
Feature: Design Token Integration

Scenario: Admin dashboard uses shared color palette
  Given I access the Edge Admin dashboard
  When the page loads
  Then the header displays the purple-to-pink gradient (#8b5cf6 to #ec4899)
  And card backgrounds use the soft purple tint (#faf5ff)
  And status colors match the consumer app (green/orange/gray)

Scenario: Typography matches consumer app
  Given I view the admin dashboard
  When I inspect text elements
  Then headings use Nunito font family
  And body text uses Inter font family
  And font sizes follow the defined type scale

Scenario: Spacing and layout use design tokens
  Given the admin dashboard renders
  When I inspect component spacing
  Then padding and margins follow the 4px base unit system
  And card border-radius is 16px
  And shadows match the purple-tinted box-shadow

Scenario: Interactive elements follow design patterns
  Given I interact with buttons and controls
  When I hover or focus on them
  Then they display consistent hover/focus states
  And transitions use 150-200ms ease-out timing
```

### Technical Notes

**Shared CSS Variables (from consumer app):**
```css
:root {
  /* Primary Colors */
  --snack-purple: #8b5cf6;
  --candy-pink: #ec4899;
  --fresh-green: #22c55e;
  --warning-orange: #f97316;
  --empty-gray: #9ca3af;

  /* Background */
  --bg-light: #faf5ff;
  --card-bg: #ffffff;

  /* Typography */
  --font-display: 'Nunito', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Effects */
  --radius-card: 16px;
  --shadow-card: 0 4px 6px -1px rgba(139, 92, 246, 0.1),
                 0 2px 4px -1px rgba(139, 92, 246, 0.06);
}
```

**Flask Template Integration:**
- Add shared CSS file to `admin/static/styles.css`
- Update `base.html` template with font imports (Google Fonts)
- Apply design tokens to existing HTMX components

### Definition of Done

- [ ] CSS variables defined in admin portal stylesheet
- [ ] Google Fonts (Nunito, Inter) loaded in base template
- [ ] Header displays gradient background
- [ ] Cards use proper border-radius and shadows
- [ ] All spacing follows 4px base unit
- [ ] Colors match consumer PWA exactly

### Dependencies

- **Blocked by:** None
- **Blocks:** E6-S2, E6-S3, E6-S4, E6-S5

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - CSS integration with existing Flask templates

### Files to Modify

- `edge/admin/static/styles.css` (create or update)
- `edge/admin/templates/base.html`
- `edge/admin/templates/index.html`

---

## E6-S2: Dashboard Status Cards Redesign

### User Story

**As a** system administrator,
**I want** the dashboard status cards to display detection status, inventory counts, and system health in a visually appealing way,
**So that** I can quickly assess system state at a glance with the same delight as the consumer experience.

### Acceptance Criteria

```gherkin
Feature: Dashboard Status Cards

Scenario: Detection status card displays correctly
  Given the detection service is running
  When I view the dashboard
  Then the detection status card shows a gradient background
  And displays the current FPS with large, bold typography
  And shows a status badge (Running/Stopped) with color + icon
  And the card animates on load with a subtle entrance effect

Scenario: Inventory summary card shows counts
  Given items are detected
  When I view the inventory summary card
  Then it displays total items tracked
  And shows a breakdown by status (in stock, low, empty)
  And uses the same status colors as consumer app
  And counts are displayed in large, prominent typography

Scenario: System health card indicates device state
  Given the edge device is operational
  When I view the system health card
  Then it shows CPU/memory usage with visual indicators
  And displays camera status (connected/disconnected)
  And shows last API sync timestamp
  And uses appropriate status colors for health states

Scenario: Cards have playful interactions
  Given I hover over a status card
  When my cursor enters the card area
  Then the card slightly elevates (subtle transform)
  And the shadow deepens slightly
  And the transition is smooth (200ms)
```

### Technical Notes

**Card Structure (HTMX):**
```html
<div class="status-card status-card--running" hx-get="/status" hx-trigger="every 5s">
  <div class="status-card__icon">
    <!-- SVG icon -->
  </div>
  <div class="status-card__content">
    <h3 class="status-card__title">Detection Status</h3>
    <div class="status-card__value">4.5 FPS</div>
    <div class="status-badge status-badge--success">
      <span class="status-badge__icon">✓</span>
      <span class="status-badge__text">Running</span>
    </div>
  </div>
</div>
```

**CSS Classes:**
```css
.status-card {
  background: linear-gradient(145deg, #faf5ff 0%, #f0fdf4 100%);
  border-radius: var(--radius-card);
  padding: var(--space-lg);
  box-shadow: var(--shadow-card);
  transition: transform 200ms ease-out, box-shadow 200ms ease-out;
}

.status-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 12px -2px rgba(139, 92, 246, 0.15);
}
```

### Definition of Done

- [ ] Three status cards implemented (Detection, Inventory, Health)
- [ ] Cards use gradient backgrounds per status
- [ ] Status badges show color + icon + text
- [ ] Large typography for key metrics
- [ ] Hover effects with subtle elevation
- [ ] HTMX polling for live updates (every 5 seconds)

### Dependencies

- **Blocked by:** E6-S1 (Design Tokens)
- **Blocks:** None

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - requires template restructuring

### Files to Modify

- `edge/admin/templates/index.html`
- `edge/admin/static/styles.css`
- `edge/admin/app.py` (status endpoint enhancements)

---

## E6-S3: Camera Preview & ROI Configuration Polish

### User Story

**As a** system administrator,
**I want** the camera preview and ROI configuration interface to feel modern and intuitive,
**So that** setting up the detection zone is a pleasant, frustration-free experience.

### Acceptance Criteria

```gherkin
Feature: Camera Preview Polish

Scenario: Camera preview has polished container
  Given I navigate to the camera preview section
  When the MJPEG stream displays
  Then the preview is contained in a card with rounded corners
  And has a subtle drop shadow
  And displays a "Live" badge with pulsing animation
  And shows camera resolution and FPS in the footer

Scenario: ROI selection is visually clear
  Given I'm configuring the ROI
  When I drag to select the region
  Then the selection area has a vibrant purple border (#8b5cf6)
  And the area outside ROI is dimmed (50% opacity overlay)
  And corner handles are visible and styled consistently
  And the selection smoothly animates as I drag

Scenario: ROI controls are intuitive
  Given the ROI is configured
  When I view the control panel
  Then "Save ROI" button uses the primary gradient
  And "Reset" button is styled as secondary
  And current ROI coordinates display in a formatted way
  And success/error feedback uses toast notifications

Scenario: Preview section has loading state
  Given the camera is initializing
  When the stream is not yet available
  Then a skeleton loader displays in the preview area
  And a spinner with the brand color indicates loading
  And status text shows "Connecting to camera..."
```

### Technical Notes

**Preview Container:**
```html
<div class="camera-preview">
  <div class="camera-preview__header">
    <span class="camera-preview__title">Camera Feed</span>
    <span class="live-badge">
      <span class="live-badge__dot"></span>
      LIVE
    </span>
  </div>
  <div class="camera-preview__stream">
    <img src="/preview" alt="Camera preview" />
    <div class="roi-overlay" id="roi-selection"></div>
  </div>
  <div class="camera-preview__footer">
    <span>1920×1080 @ 30 FPS</span>
  </div>
</div>
```

**Live Badge Animation:**
```css
.live-badge__dot {
  width: 8px;
  height: 8px;
  background: var(--fresh-green);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}
```

**ROI Selection Styling:**
```css
.roi-overlay {
  position: absolute;
  border: 3px solid var(--snack-purple);
  background: rgba(139, 92, 246, 0.1);
  border-radius: 8px;
}

.roi-handle {
  width: 12px;
  height: 12px;
  background: var(--snack-purple);
  border: 2px solid white;
  border-radius: 50%;
}
```

### Definition of Done

- [ ] Camera preview in styled card with header/footer
- [ ] Live badge with pulsing green dot animation
- [ ] ROI selection with purple border and dimmed exterior
- [ ] Corner handles for ROI adjustment
- [ ] Save/Reset buttons with proper styling
- [ ] Toast notifications for success/error feedback
- [ ] Loading skeleton while camera connects

### Dependencies

- **Blocked by:** E6-S1 (Design Tokens)
- **Blocks:** None

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - JavaScript interaction for ROI drag

### Files to Modify

- `edge/admin/templates/roi.html`
- `edge/admin/static/styles.css`
- `edge/admin/static/roi.js` (create or update)
- `edge/admin/app.py` (preview endpoint)

---

## E6-S4: Dark Mode Support for Admin Portal

### User Story

**As a** system administrator working in various lighting conditions,
**I want** the admin dashboard to support dark mode,
**So that** I can comfortably use it in low-light environments and it matches my system preferences.

### Acceptance Criteria

```gherkin
Feature: Dark Mode Support

Scenario: Admin dashboard detects system preference
  Given my operating system has dark mode enabled
  When I open the admin dashboard
  Then the interface automatically displays in dark mode
  And no manual toggle is required

Scenario: Dark mode colors are correct
  Given dark mode is active
  When the dashboard displays
  Then background color is #1a1625 (dark purple)
  And card backgrounds are #2d2640
  And text colors adjust for readability (#f9fafb primary, #9ca3af secondary)

Scenario: Header gradient remains vibrant
  Given dark mode is active
  When the header displays
  Then the purple-to-pink gradient is still visible and vibrant
  And contrasts well against the dark background

Scenario: Camera preview adapts to dark mode
  Given dark mode is active
  When I view the camera preview
  Then the preview container has dark background
  And the live badge and controls remain visible
  And ROI selection colors are still distinguishable

Scenario: Smooth transition on theme change
  Given I toggle my system theme
  When dark mode activates or deactivates
  Then colors transition smoothly (~200ms)
  And there is no flash of incorrect colors
```

### Technical Notes

**Dark Mode CSS Variables:**
```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-light: #1a1625;
    --card-bg: #2d2640;
    --text-primary: #f9fafb;
    --text-secondary: #9ca3af;
    --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.3),
                   0 2px 4px -1px rgba(0, 0, 0, 0.2);
  }
}
```

**Smooth Transition:**
```css
body,
.status-card,
.camera-preview {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}
```

### Definition of Done

- [ ] Dark mode CSS variables defined
- [ ] `prefers-color-scheme: dark` media query implemented
- [ ] Background changes to #1a1625 in dark mode
- [ ] Cards change to #2d2640
- [ ] Text colors adjust correctly
- [ ] Header gradient remains vibrant
- [ ] Camera preview adapts properly
- [ ] Smooth transition on theme change
- [ ] All text meets WCAG contrast requirements

### Dependencies

- **Blocked by:** E6-S1 (Design Tokens), E6-S2 (Status Cards), E6-S3 (Camera Preview)
- **Blocks:** E6-S6

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - CSS additions, no structural changes

### Files to Modify

- `edge/admin/static/styles.css`
- `edge/admin/templates/base.html` (meta theme-color)

---

## E6-S5: Responsive Layout for Admin Portal

### User Story

**As a** system administrator accessing the dashboard from different devices,
**I want** the admin interface to adapt to my screen size,
**So that** I can manage the system from my phone, tablet, or desktop.

### Acceptance Criteria

```gherkin
Feature: Responsive Admin Layout

Scenario: Desktop layout (>1024px)
  Given I'm viewing on a desktop
  When the dashboard displays
  Then status cards are in a 3-column grid
  And camera preview takes 2/3 width
  And controls panel takes 1/3 width
  And navigation is horizontal

Scenario: Tablet layout (640-1024px)
  Given I'm viewing on a tablet
  When the dashboard displays
  Then status cards are in a 2-column grid
  And camera preview is full-width
  And controls panel is below preview
  And navigation is horizontal with condensed labels

Scenario: Mobile layout (<640px)
  Given I'm viewing on a mobile device
  When the dashboard displays
  Then status cards stack vertically (1 column)
  And camera preview is full-width
  And all sections stack vertically
  And navigation becomes a hamburger menu

Scenario: Touch targets are adequate on mobile
  Given I'm on a touch device
  When I interact with buttons and controls
  Then all touch targets are at least 44x44px
  And there is adequate spacing between interactive elements
```

### Technical Notes

**Responsive Grid:**
```css
.dashboard-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.camera-section {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: 1fr;
}

@media (min-width: 1024px) {
  .camera-section {
    grid-template-columns: 2fr 1fr;
  }
}
```

**Mobile Navigation:**
```html
<nav class="admin-nav">
  <button class="admin-nav__toggle" aria-label="Menu">
    <svg><!-- hamburger icon --></svg>
  </button>
  <ul class="admin-nav__list">
    <li><a href="/">Dashboard</a></li>
    <li><a href="/roi">ROI Config</a></li>
    <li><a href="/status">Status</a></li>
  </ul>
</nav>
```

### Definition of Done

- [ ] 3-column grid on desktop, 2-column on tablet, 1-column on mobile
- [ ] Camera section adapts (side-by-side on desktop, stacked on mobile)
- [ ] Navigation collapses to hamburger on mobile
- [ ] Touch targets minimum 44x44px
- [ ] Adequate spacing between interactive elements
- [ ] Viewport meta tag properly configured

### Dependencies

- **Blocked by:** E6-S1 (Design Tokens)
- **Blocks:** None

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - CSS layout adjustments

### Files to Modify

- `edge/admin/static/styles.css`
- `edge/admin/templates/base.html`
- `edge/admin/templates/index.html`

---

## E6-S6: Accessibility Compliance for Admin Portal

### User Story

**As a** system administrator with accessibility needs,
**I want** the admin dashboard to meet WCAG 2.1 Level AA standards,
**So that** I can effectively use the interface regardless of visual or motor abilities.

### Acceptance Criteria

```gherkin
Feature: Accessibility Compliance

Scenario: Color contrast meets requirements
  Given any text element in the admin portal
  When I check its contrast ratio
  Then normal text has at least 4.5:1 contrast
  And large text has at least 3:1 contrast

Scenario: Status not conveyed by color alone
  Given any status indicator
  When it displays
  Then it shows color AND icon AND text
  And status is understandable without seeing colors

Scenario: Keyboard navigation works
  Given I'm navigating with keyboard
  When I tab through the interface
  Then all interactive elements are reachable
  And focus indicators are visible (purple focus ring)
  And focus order is logical

Scenario: Screen reader announces correctly
  Given I'm using a screen reader
  When I navigate the dashboard
  Then page structure uses proper landmarks (header, main, nav)
  And buttons have accessible labels
  And status updates are announced via ARIA live regions

Scenario: Animations respect user preferences
  Given prefers-reduced-motion is enabled
  When the page displays
  Then no motion animations play
  And the live badge dot does not pulse
  And hover transitions are instant
```

### Technical Notes

**Focus Styling:**
```css
:focus-visible {
  outline: 2px solid var(--snack-purple);
  outline-offset: 2px;
  border-radius: 4px;
}

:focus:not(:focus-visible) {
  outline: none;
}
```

**ARIA Live Region for Status:**
```html
<div aria-live="polite" aria-atomic="true" class="sr-only" id="status-announcer">
  <!-- Dynamic status updates announced here -->
</div>
```

**Reduced Motion:**
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Semantic Structure:**
```html
<header role="banner"><!-- Header --></header>
<nav role="navigation" aria-label="Main navigation"><!-- Nav --></nav>
<main role="main">
  <h1>Dashboard</h1>
  <section aria-labelledby="status-heading">
    <h2 id="status-heading">System Status</h2>
    <!-- Status cards -->
  </section>
</main>
```

### Definition of Done

- [ ] All text meets 4.5:1 contrast ratio
- [ ] Status uses color + icon + text (not color alone)
- [ ] All interactive elements have visible focus indicators
- [ ] Keyboard navigation reaches all controls
- [ ] Screen reader can navigate with proper landmarks
- [ ] ARIA live regions announce status updates
- [ ] Animations respect `prefers-reduced-motion`
- [ ] Semantic HTML with proper heading hierarchy

### Dependencies

- **Blocked by:** E6-S1 through E6-S5 (all visual work complete)
- **Blocks:** None (final validation story)

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - audit and fix existing components

### Files to Modify

- `edge/admin/static/styles.css`
- `edge/admin/templates/base.html`
- `edge/admin/templates/index.html`
- `edge/admin/templates/roi.html`

---

## Epic 6 Summary

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| E6-S1 | Design Token Integration | 3 | None |
| E6-S2 | Dashboard Status Cards Redesign | 5 | E6-S1 |
| E6-S3 | Camera Preview & ROI Polish | 5 | E6-S1 |
| E6-S4 | Dark Mode Support | 3 | E6-S1, E6-S2, E6-S3 |
| E6-S5 | Responsive Layout | 3 | E6-S1 |
| E6-S6 | Accessibility Compliance | 3 | E6-S1 through E6-S5 |
| **Total** | | **22** | |

**Dependency Graph:**
```
E6-S1 Design Token Integration
    │
    ├──► E6-S2 Dashboard Status Cards
    │         │
    │         └──────────────┐
    │                        │
    ├──► E6-S3 Camera Preview │
    │         │               │
    │         └──────────────┼──► E6-S4 Dark Mode
    │                        │
    ├──► E6-S5 Responsive Layout
    │
    └──────────────────────────────► E6-S6 Accessibility (final)

Execution Order:
1. E6-S1 (foundation)
2. E6-S2, E6-S3, E6-S5 (can parallelize)
3. E6-S4 (after E6-S2 and E6-S3)
4. E6-S6 (final validation)
```

**Milestone Checkpoint:** After Epic 6 completion, the Edge Admin dashboard should be visually indistinguishable in quality from the consumer PWA. Both interfaces should feel like parts of the same cohesive product, using identical design tokens, color palette, and interaction patterns.

---

## Design Reference Summary

### From FoodInsight UX Specification

| Element | Value | Usage in Admin |
|---------|-------|----------------|
| **Header Gradient** | `linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)` | Admin header |
| **Card Background** | `#ffffff` (light), `#2d2640` (dark) | Status cards, preview container |
| **Page Background** | `#faf5ff` (light), `#1a1625` (dark) | Body background |
| **Border Radius** | `16px` | Cards, buttons, containers |
| **Font Display** | Nunito 800 | Headings, large metrics |
| **Font Body** | Inter 400-600 | Body text, labels |
| **Status Green** | `#22c55e` | Running, success states |
| **Status Orange** | `#f97316` | Warnings, low stock |
| **Status Gray** | `#9ca3af` | Stopped, empty states |

### Architecture Context

The Edge Admin Portal runs on the same Raspberry Pi as the detection service:
- **Framework:** Flask + HTMX
- **Port:** 8080 (local network only)
- **Access:** LAN only, not exposed to internet
- **Auth:** None required (local admin access)

---

**Version History:**

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-13 | 1.0 | Initial Epic creation | Sarah (PO) via BMAD |

---

_This Epic was created using the BMAD create-story workflow. The Edge Admin UX Revamp brings the admin experience up to the same "Playful & Vibrant" standard as the consumer PWA._
