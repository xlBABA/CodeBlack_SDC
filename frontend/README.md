# Mustaqbal AI — frontend

UI prototype for the SDC Hackathon 2026 (Domain 1). All data is mock (`src/mocks`);
API integration is the next step.

Stack: Vite + React 19 + TypeScript (strict) + Tailwind CSS v4 + shadcn/ui + React Router,
GSAP (ScrollTrigger, MotionPath) for motion, Lenis for smooth scrolling on the landing page.

## Run

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build
npm run lint       # oxlint
```

Copy `.env.example` to `.env.local` to set `VITE_API_BASE_URL`.

Mock states: add `?mock=empty`, `?mock=404` or `?mock=503` to any app URL.

## Map

| Path | What |
|---|---|
| `src/config/product.ts` | product name (also injected into `index.html`) |
| `src/styles/tokens.css` | light/dark tokens, landing palette, 4 accent colours, 17 SDG colours |
| `src/components/brand.tsx`, `public/brand/` | Mustaqbal AI mark and wordmark |
| `src/lib/theme.ts` | theme + accent store, circular theme-switch transition |
| `src/components/layout/*` | app shell: top pill tabs, floating dock, mobile tabs, route transition |
| `src/components/dashboard/*` | overview widgets |
| `src/components/landing/*` | intro, hero, manifesto, horizontal journey, report section, numbers, footer |
| `src/mocks/*` | APIEnvelope-shaped fixtures and a mock client with empty / 404 / 503 states |
| `src/pages/*` | routes (`/start`, `/roles/:roleId`, `/methodology` are placeholders for now) |
