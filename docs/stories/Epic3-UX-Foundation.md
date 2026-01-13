# Epic 3: UX Foundation - Design System & Core Components

**Epic Goal:** Establish the Playful & Vibrant design system foundation with updated Tailwind tokens, gradient header, redesigned snack cards, and multi-state status indicators.

**PRD Reference:** [[FoodInsight PRD]]
**Architecture Reference:** [[FoodInsight Solution Architecture]]
**UX Reference:** [[FoodInsight UX Specification]]

**Epic Acceptance Criteria:**
- [x] All design tokens from UX spec implemented in Tailwind config
- [x] Header displays purple-to-pink gradient with branding
- [x] SnackCards show gradient backgrounds per stock state (high/low/out)
- [x] Status indicators use color + icon + text (WCAG compliant)
- [ ] Visual appearance matches UX spec wireframes

---

## E3-S1: Design Tokens and Tailwind Configuration

### User Story

**As a** developer,
**I want** the Tailwind CSS configuration updated with the Playful & Vibrant design system tokens,
**So that** all components can use consistent colors, typography, and spacing from the UX specification.

### Acceptance Criteria

```gherkin
Feature: Design System Tokens

Scenario: Primary colors are available
  Given the Tailwind config is updated
  When I use color classes in components
  Then "snack-purple" (#8b5cf6) is available
  And "candy-pink" (#ec4899) is available
  And "fresh-green" (#22c55e) is available
  And "warning-orange" (#f97316) is available
  And "empty-gray" (#9ca3af) is available

Scenario: Gradient utilities work
  Given the design tokens are configured
  When I apply "bg-header-gradient" class
  Then a 135deg gradient from purple to pink renders
  And "bg-card-available", "bg-card-warning", "bg-card-empty" gradients work

Scenario: Typography is configured
  Given Google Fonts are loaded
  When I apply font classes
  Then Nunito renders for display text (font-display)
  And Inter renders for body text (font-body)
  And type scale matches spec (app-title 28px/800, count-display 48px/800)

Scenario: Dark mode colors are defined
  Given dark mode is enabled
  When I check semantic colors
  Then background is #1a1625
  And card background is #2d2640
  And text colors have proper contrast
```

### Technical Notes

**Tailwind v4 Configuration:**
- Uses CSS-first configuration via `@theme` directive
- Fonts loaded via Google Fonts CDN in index.html
- CSS custom properties enable animation color references

**Color Palette:**
| Name | Hex | Usage |
|------|-----|-------|
| Snack Purple | #8b5cf6 | Primary brand, header gradient start |
| Candy Pink | #ec4899 | Header gradient end |
| Fresh Green | #22c55e | In-stock status |
| Warning Orange | #f97316 | Low stock alerts |
| Empty Gray | #9ca3af | Out of stock |

**Font Stack:**
```css
--font-display: 'Nunito', system-ui, sans-serif;
--font-body: 'Inter', system-ui, sans-serif;
```

### Definition of Done

- [x] All primary colors added to Tailwind config
- [x] Gradient utilities working (header, card states)
- [x] Google Fonts loading (Nunito, Inter)
- [x] Type scale tokens implemented
- [x] Dark mode semantic colors defined
- [x] CSS custom properties available for animations
- [ ] Test page showing all color swatches created

### Visual Testing Checklist

- [ ] Create test page showing all color swatches
- [ ] Verify gradient backgrounds render correctly
- [ ] Confirm font families load (check network tab)
- [ ] Test responsive breakpoints match spec
- [ ] Verify dark mode colors toggle correctly

### Dependencies

- **Blocked by:** None (first story)
- **Blocks:** E3-S2, E3-S3, E3-S4

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - configuration work

### Files to Modify

- `app/src/assets/main.css`
- `app/vite.config.ts`
- `app/index.html`

---

## E3-S2: Gradient Header with Branding

### User Story

**As a** user,
**I want** a vibrant purple-to-pink gradient header with the FoodInsight logo and location badge,
**So that** the app feels playful and branded, making the break room experience more delightful.

### Acceptance Criteria

```gherkin
Feature: Gradient Header

Scenario: Header displays gradient background
  Given I open the app
  When the header renders
  Then the background shows purple-to-pink gradient at 135deg
  And the gradient starts at #8b5cf6 and ends at #ec4899

Scenario: Branding elements display correctly
  Given the header is visible
  Then I see a popcorn emoji before "FoodInsight"
  And the title uses Nunito font at 28px weight 800
  And a pin emoji appears before the location name
  And the location text is smaller and secondary

Scenario: Header adapts to screen size
  Given I view on mobile (<640px)
  Then the header is full-width
  And title and location are stacked vertically
  When I view on tablet+ (>=640px)
  Then the header has rounded corners with margin
  And title and location are inline

Scenario: Text meets accessibility contrast
  Given the gradient background is displayed
  When I check text contrast
  Then white text on gradient exceeds 4.5:1 ratio
```

### Technical Notes

**Current Header (to replace):**
```vue
<header class="bg-white shadow-sm">
```

**New Header Structure:**
```vue
<header class="bg-header-gradient">
  <div class="max-w-4xl mx-auto px-4 py-4">
    <h1 class="text-2xl font-display font-extrabold text-white">
      🍿 FoodInsight
    </h1>
    <p class="text-sm text-white/80">📍 {{ location }}</p>
  </div>
</header>
```

**Responsive Adaptation:**
| Mobile | Tablet/Desktop |
|--------|----------------|
| Full-width gradient | Rounded with margin |
| Stacked: Title above location | Inline: Title + location |
| Larger touch targets | Standard sizing |

### Definition of Done

- [x] Header displays gradient background
- [x] Popcorn emoji + "FoodInsight" title rendered
- [x] Pin emoji + location displayed
- [x] Full-width on mobile, rounded on desktop
- [x] Text contrast meets WCAG 4.5:1
- [ ] Dark mode appearance verified

### Visual Testing Checklist

- [ ] Screenshot header at 375px width (mobile)
- [ ] Screenshot header at 768px width (tablet)
- [ ] Screenshot header at 1280px width (desktop)
- [ ] Verify gradient direction matches spec (135deg)
- [ ] Check text readability on gradient background

### Dependencies

- **Blocked by:** E3-S1 (Design Tokens)
- **Blocks:** None

### Complexity

**Points:** 2 (Small)
**Risk:** Low - styling changes only

### Files to Modify

- `app/src/App.vue`

---

## E3-S3: SnackCard Component Redesign

### User Story

**As a** user,
**I want** snack cards with gradient backgrounds, large centered icons, and prominent count displays,
**So that** I can quickly see snack availability at a glance with a delightful visual experience.

### Acceptance Criteria

```gherkin
Feature: Redesigned Snack Cards

Scenario: Card layout matches new design
  Given a snack card is displayed
  Then the emoji icon is large and centered at top (~40-48px)
  And the snack name appears below the icon
  And the count is prominent (48px font, weight 800)
  And the status badge is at the bottom

Scenario: High stock card displays correctly
  Given a snack has count > 3
  When the card renders
  Then background gradient is purple-green tint (#faf5ff to #f0fdf4)
  And the count displays in large bold text
  And status shows "Available" with green badge

Scenario: Low stock card displays warning state
  Given a snack has count 1-3
  When the card renders
  Then background gradient is warm warning (#fffbeb to #fff7ed)
  And status shows "Low" with orange badge

Scenario: Out of stock card displays empty state
  Given a snack has count 0
  When the card renders
  Then background gradient is gray (#f9fafb to #f3f4f6)
  And the card has grayscale appearance
  And message shows "come back soon"
  And status shows "Empty" with gray badge

Scenario: Card has correct dimensions
  Given any snack card
  Then min-height is 160px
  And border-radius is 16px
  And shadow has purple tint

Scenario: Card hover state on desktop
  Given I hover over a card on desktop
  Then the shadow increases
  And card lifts slightly (translateY -2px)
```

### Technical Notes

**Stock Level Logic:**
```typescript
const stockLevel = computed(() => {
  if (props.item.count === 0) return 'out'
  if (props.item.count <= 3) return 'low'
  return 'high'
})
```

**Card Gradients:**
| State | Gradient |
|-------|----------|
| High Stock | `linear-gradient(145deg, #faf5ff 0%, #f0fdf4 100%)` |
| Low Stock | `linear-gradient(145deg, #fffbeb 0%, #fff7ed 100%)` |
| Out of Stock | `linear-gradient(145deg, #f9fafb 0%, #f3f4f6 100%)` |

**Card Layout Structure:**
```
┌─────────────────────────┐
│  🍫  ←── Snack Icon     │
│       (large, centered) │
│                         │
│  Candy Bar ←── Name     │
│                         │
│  ┌─────┐                │
│  │  5  │ ←── Count      │
│  └─────┘    (prominent) │
│                         │
│  ✓ In Stock ←── Status  │
└─────────────────────────┘
```

### Definition of Done

- [x] Card layout restructured (icon top, count prominent)
- [x] Three gradient states implemented (high/low/out)
- [x] Count uses 48px/800 font
- [x] Card dimensions match spec (160px min-height, 16px radius)
- [x] Purple-tint shadow applied
- [x] Hover state working on desktop
- [x] "Come back soon" message for out of stock

### Visual Testing Checklist

- [ ] Screenshot card in "In Stock (High)" state (count > 3)
- [ ] Screenshot card in "Low Stock" state (count 1-3)
- [ ] Screenshot card in "Out of Stock" state (count 0)
- [ ] Verify gradient directions match spec (145deg)
- [ ] Check count font size is 48px
- [ ] Verify border-radius is 16px
- [ ] Test hover state on desktop browser

### Dependencies

- **Blocked by:** E3-S1 (Design Tokens)
- **Blocks:** E3-S4 (Status Indicators)

### Complexity

**Points:** 5 (Medium-Large)
**Risk:** Medium - significant component rework

### Files to Modify

- `app/src/components/SnackCard.vue`
- `app/src/types/inventory.ts` (may need stockLevel type)

---

## E3-S4: Multi-State Status Indicators

### User Story

**As a** user,
**I want** status indicators that show availability through color, icon, AND text,
**So that** I can understand stock status regardless of color vision and meet accessibility requirements.

### Acceptance Criteria

```gherkin
Feature: Accessible Status Indicators

Scenario: Available status displays correctly
  Given a snack is in stock (count > 3)
  When the status badge renders
  Then background is green gradient (#22c55e to #16a34a)
  And a checkmark icon is visible
  And text shows "Available"
  And ARIA label reads "X items available"

Scenario: Low stock status displays correctly
  Given a snack has low stock (count 1-3)
  When the status badge renders
  Then background is orange gradient (#f97316 to #ea580c)
  And a lightning bolt icon is visible
  And text shows "Low"
  And ARIA label reads "Only X items left"

Scenario: Out of stock status displays correctly
  Given a snack is out of stock (count 0)
  When the status badge renders
  Then background is gray (#9ca3af)
  And an X mark icon is visible
  And text shows "Empty"
  And ARIA label reads "Out of stock"

Scenario: Status is accessible to screen readers
  Given any status badge
  When a screen reader reads the card
  Then the full status context is announced
  And the icon is marked as decorative (aria-hidden)
```

### Technical Notes

**StatusBadge Component Props:**
```typescript
interface StatusBadgeProps {
  status: 'available' | 'low' | 'out'
  count: number
}
```

**SVG Icons (inline for color control):**
```html
<!-- Checkmark -->
<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
  <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
</svg>

<!-- Lightning bolt -->
<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
  <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"/>
</svg>

<!-- X mark -->
<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
  <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/>
</svg>
```

**ARIA Labels:**
| Status | ARIA Label |
|--------|------------|
| Available | "{count} items available" |
| Low | "Only {count} items left" |
| Out | "Out of stock" |

### Definition of Done

- [x] StatusBadge component created
- [x] Three states with correct colors/gradients
- [x] Inline SVG icons for checkmark, lightning, X
- [x] Text labels visible for all states
- [x] ARIA labels provide full context
- [x] Icons marked as decorative
- [x] Component integrated into SnackCard

### Visual Testing Checklist

- [ ] Screenshot "Available" badge with checkmark
- [ ] Screenshot "Low Stock" badge with lightning bolt
- [ ] Screenshot "Out of Stock" badge with X mark
- [ ] Verify colors match spec hex values
- [ ] Check icon alignment with text
- [ ] Run accessibility audit (aXe or similar)
- [ ] Test with screen reader for ARIA labels

### Dependencies

- **Blocked by:** E3-S3 (SnackCard Redesign)
- **Blocks:** None in Epic 3

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - new component extraction

### Files to Modify

- `app/src/components/StatusBadge.vue` (new)
- `app/src/components/SnackCard.vue`

---

## Epic 3 Summary

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| E3-S1 | Design Tokens | 3 | None |
| E3-S2 | Header Gradient | 2 | E3-S1 |
| E3-S3 | SnackCard Redesign | 5 | E3-S1 |
| E3-S4 | Status Indicators | 3 | E3-S3 |
| **Total** | | **13** | |

**Dependency Graph:**
```
E3-S1 Design Tokens
  │
  ├──► E3-S2 Header Gradient
  │
  └──► E3-S3 SnackCard Redesign
            │
            └──► E3-S4 Status Indicators
```

**Milestone Checkpoint:** After Epic 3 completion, the app should visually match the "Current vs Proposed" comparison table in the UX specification.
