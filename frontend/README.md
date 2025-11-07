# ASX Announcements - Frontend

Next.js 15 frontend application for the ASX Announcements SaaS platform.

## Features

- 🎨 **Modern UI**: Built with Next.js 15 App Router and Tailwind CSS
- ⚡ **Performance**: Server components and client-side navigation
- 📱 **Responsive**: Works on all devices
- 🔍 **Search & Filter**: Advanced filtering by sentiment, price sensitivity
- 📊 **Data Visualization**: Stock performance and market metrics
- 🤖 **AI Insights**: Display Gemini-powered analysis results

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Date Formatting**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see `../backend/README.md`)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your backend API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
# Create production build
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── announcements/            # Announcements list page
│   │   ├── [id]/                 # Dynamic announcement detail page
│   │   │   └── page.tsx
│   │   └── page.tsx
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home page
├── components/                   # Reusable React components
│   ├── AnnouncementCard.tsx      # Announcement card component
│   └── FilterBar.tsx             # Filter bar component
├── lib/                          # Utility functions
│   └── api.ts                    # API client and types
├── public/                       # Static assets
├── .env.example                  # Environment variables template
├── next.config.ts                # Next.js configuration
├── tailwind.config.ts            # Tailwind CSS configuration
└── tsconfig.json                 # TypeScript configuration
```

## API Integration

The frontend connects to the FastAPI backend via the API client (`lib/api.ts`).

### Environment Variables

Configure the backend API URL in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Functions

```typescript
import { getAnnouncements, getAnnouncement } from '@/lib/api';

// Get paginated announcements
const data = await getAnnouncements({
  page: 1,
  page_size: 20,
  price_sensitive_only: true,
});

// Get single announcement with details
const announcement = await getAnnouncement(id);
```

## Pages

### Home (`/`)
- Landing page with feature overview
- Quick stats and call-to-action
- Links to announcements

### Announcements List (`/announcements`)
- Paginated list of all announcements
- Filter by price sensitivity and sentiment
- Announcement cards with metadata
- Navigation to detail pages

### Announcement Detail (`/announcements/[id]`)
- Full announcement details
- AI-powered analysis (summary, sentiment, insights)
- Stock performance metrics
- Link to original PDF

## Components

### `AnnouncementCard`
Displays announcement preview with:
- ASX code and company name
- Title and metadata (date, pages, file size)
- Price sensitivity badge
- Sentiment badge (if analyzed)
- Processing status

### `FilterBar`
Filter controls for announcements:
- Price sensitive toggle
- Sentiment dropdown (bullish/bearish/neutral)
- Reset filters button

## Styling

Tailwind CSS utility classes are used throughout. Key colors:

- **Primary**: Blue (`blue-600`)
- **Success**: Green (bullish sentiment)
- **Danger**: Red (bearish sentiment)
- **Warning**: Orange (price sensitive)

## TypeScript

Full TypeScript support with strict mode enabled. API types are defined in `lib/api.ts`.

## Development Tips

### Hot Reload
The dev server supports hot reload. Changes to files will automatically update the browser.

### Debugging
- Check browser console for errors
- Use React DevTools for component debugging
- Check Network tab for API calls

### Adding New Pages
1. Create new file in `app/` directory
2. Export default React component
3. Navigation will be automatic

## Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

### Manual Deployment
```bash
# Build
npm run build

# Start production server
npm start
```

Set environment variables in your deployment platform:
- `NEXT_PUBLIC_API_URL`: Your production API URL

## Future Enhancements

- [ ] Real-time updates via WebSockets
- [ ] Advanced charts for stock performance
- [ ] User authentication with NextAuth.js
- [ ] Subscription management UI
- [ ] Watchlist functionality
- [ ] Mobile app (React Native)

## Support

- **Documentation**: See `backend/API_README.md` for API reference
- **GitHub**: https://github.com/tanveeruddin/asx_announcement_scraper

---

**Last Updated**: 2025-11-07
**Version**: 0.1.0
