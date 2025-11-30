# DropInsight - Dashboard Frontend

Internal dashboard for the Dropshipping Platform Market Intelligence system.

## Overview

This is a **Next.js 14** application using the App Router, built with:

- **React 18** - UI library
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Recharts** - Charts and visualizations
- **Lucide React** - Icons

## Quick Start

### Prerequisites

- Node.js 18+ (recommended: 20+)
- npm or yarn
- Backend API running (FastAPI)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local with your API URL
```

### Environment Variables

Create a `.env.local` file:

```env
# Backend API Base URL (required)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Optional: Admin API Key for protected endpoints
ADMIN_API_KEY=your-admin-key
```

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx            # Root layout with sidebar
│   ├── page.tsx              # Dashboard page (/)
│   ├── globals.css           # Global styles + Tailwind
│   └── pages/
│       ├── page.tsx          # Pages list (/pages)
│       └── [pageId]/
│           └── page.tsx      # Page detail (/pages/:id)
│
├── components/
│   ├── ui/                   # Reusable UI components
│   │   ├── Badge.tsx         # Tier/Match/Status badges
│   │   ├── Button.tsx        # Button variants
│   │   ├── Card.tsx          # Card container
│   │   ├── Input.tsx         # Form input
│   │   ├── KpiTile.tsx       # KPI metric tiles
│   │   ├── LoadingState.tsx  # Loading/Empty/Error states
│   │   ├── Select.tsx        # Dropdown select
│   │   └── Table.tsx         # Data table + pagination
│   ├── layout/               # Layout components
│   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   ├── Header.tsx        # Page header
│   │   └── Layout.tsx        # Main layout wrapper
│   └── charts/               # Chart components
│       └── ScoreChart.tsx    # Score evolution line chart
│
├── lib/
│   ├── api/                  # API client layer
│   │   └── client.ts         # Typed fetch functions
│   └── types/                # TypeScript types
│       └── api.ts            # Backend schema types
│
├── __tests__/                # Jest tests
│   └── components/ui/
│       ├── Badge.test.tsx
│       └── Table.test.tsx
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── next.config.mjs
└── jest.config.js
```

## Available Routes

| Route | Description |
|-------|-------------|
| `/` | Dashboard with KPIs and top pages |
| `/pages` | Paginated list of all tracked pages with filters |
| `/pages/[pageId]` | Detailed page view with metrics history and product insights |
| `/watchlists` | (Placeholder) Watchlist management |
| `/alerts` | (Placeholder) Alerts feed |

## API Integration

The frontend communicates with the FastAPI backend through a typed API client.

### Available API Functions

```typescript
import {
  getTopPages,          // GET /pages/top
  getRankedPages,       // GET /pages/ranked
  getPageDetails,       // GET /pages/{page_id}
  getPageScore,         // GET /pages/{page_id}/score
  getPageMetricsHistory, // GET /pages/{page_id}/metrics/history
  getPageProductInsights, // GET /pages/{page_id}/products/insights
  getPageAlerts,        // GET /alerts/{page_id}
  getRecentAlerts,      // GET /alerts
} from "@/lib/api";
```

### Type Safety

All API responses are strongly typed using TypeScript interfaces that mirror the backend Pydantic schemas:

```typescript
import type {
  PageResponse,
  RankedShopsResponse,
  PageMetricsHistoryResponse,
  PageProductInsightsResponse,
} from "@/lib/types/api";
```

## Components

### UI Components

- **TierBadge** - Displays tier classification (XXL, XL, L, M, S, XS)
- **MatchBadge** - Displays match strength (strong, medium, weak, none)
- **Table** - Generic data table with sorting, pagination support
- **KpiTile** - Large metric display card
- **Card** - Content container with header/body sections

### Example Usage

```tsx
import { TierBadge, Table, KpiTile } from "@/components/ui";

// Tier badge
<TierBadge tier="XXL" size="lg" />

// KPI tile
<KpiTile
  label="Total Pages"
  value={1234}
  icon={<Store />}
  trend={{ value: 12, isPositive: true }}
/>

// Data table
<Table
  columns={columns}
  data={items}
  keyExtractor={(item) => item.id}
  onRowClick={handleClick}
/>
```

## Testing

```bash
# Run tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

## Design System

### Colors

- **Background**: `slate-950` (darkest), `slate-900` (cards)
- **Text**: `slate-100` (primary), `slate-400` (secondary), `slate-500` (muted)
- **Accent**: `blue-500/600` (primary actions)

### Tier Colors

| Tier | Color |
|------|-------|
| XXL | Green |
| XL | Lime |
| L | Yellow |
| M | Orange |
| S | Red |
| XS | Gray |

## TODOs / Planned Features

- [ ] Real-time alerts feed
- [ ] Watchlist management UI
- [ ] Ads gallery/preview section
- [ ] Backend endpoint for dashboard stats aggregate
- [ ] Backend endpoint for last snapshot date
- [ ] Search functionality across all pages
- [ ] Export data to CSV/Excel
- [ ] Dark/Light theme toggle

## Development Notes

### Adding New API Endpoints

1. Add TypeScript types in `lib/types/api.ts`
2. Add fetch function in `lib/api/client.ts`
3. Export from `lib/api/index.ts`

### Adding New Pages

1. Create route in `app/` directory
2. Use `PageContent` wrapper for consistent layout
3. Use `Header` component for page title

### Adding New Components

1. Create component in `components/ui/` or appropriate subfolder
2. Export from `components/ui/index.ts`
3. Add tests in `__tests__/components/`

## Version

Dashboard v0.1.0 - Sprint 8 Release
