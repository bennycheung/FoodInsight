# FoodInsight Consumer PWA

Vue 3 Progressive Web App for viewing snack inventory in real-time.

## Features

- **Real-time Inventory**: Auto-refreshes every 30 seconds
- **Responsive Grid**: Snack cards adapt to screen size (2-3 columns)
- **Stock Indicators**: Green "Available" / Gray "Empty" badges
- **Offline Support**: Service worker caches for offline viewing
- **Installable**: Add to home screen on mobile devices
- **Lightweight**: 33KB gzipped bundle

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Vue 3 (Composition API) |
| Build Tool | Vite 7.x |
| State | Pinia |
| Styling | Tailwind CSS v4 |
| PWA | vite-plugin-pwa |
| Package Manager | bun |

## Quick Start

```bash
# Install dependencies
bun install

# Start development server
bun run dev

# Build for production
bun run build

# Preview production build
bun run preview
```

## Environment Variables

Create `.env` file:

```bash
# API server URL
VITE_API_URL=http://localhost:8000

# Company identifier
VITE_COMPANY=demo

# Machine ID to display
VITE_MACHINE_ID=breakroom-1
```

## Project Structure

```
app/
├── src/
│   ├── App.vue                    # Root component
│   ├── main.ts                    # Entry point
│   ├── views/
│   │   └── InventoryView.vue      # Main inventory display
│   ├── components/
│   │   ├── SnackCard.vue          # Individual snack item
│   │   ├── SkeletonCard.vue       # Loading placeholder
│   │   ├── LastUpdated.vue        # Timestamp display
│   │   ├── OfflineIndicator.vue   # Network status
│   │   └── PWAUpdatePrompt.vue    # Update notification
│   ├── stores/
│   │   └── inventory.ts           # Pinia inventory store
│   ├── composables/
│   │   └── useAutoRefresh.ts      # Polling logic
│   ├── types/
│   │   └── inventory.ts           # TypeScript interfaces
│   └── assets/
│       └── main.css               # Tailwind imports
├── public/
│   └── icons/                     # PWA icons (TODO)
├── vite.config.ts                 # Vite + PWA config
└── package.json
```

## Local Development

The app connects to the FastAPI backend at `VITE_API_URL`. For local testing:

1. Start the backend server (see `../server/README.md`)
2. Start this app with `bun run dev`
3. Open http://localhost:5173

The backend has a mock router that returns sample inventory data, so Firestore is not required for local development.

## PWA Features

- **Service Worker**: Caches assets for offline use
- **Manifest**: Enables "Add to Home Screen"
- **Icons**: 192x192 and 512x512 (TODO: add actual icons)
- **Runtime Caching**: API responses cached with NetworkFirst strategy

## Deployment

Deploy to Cloudflare Pages:

```bash
bun run build
wrangler pages deploy dist --project-name=foodinsight
```

Or any static hosting service (Vercel, Netlify, etc.).

## Related

- [FoodInsight Server](../server/README.md) - FastAPI backend
- [FoodInsight Edge](../README.md) - Edge detection device
