import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router'
import { CurtainProvider } from '@/components/curtain'
import { AppShell } from '@/components/layout/app-shell'
import { ToastProvider } from '@/components/ui/toast'
import { TooltipProvider } from '@/components/ui/tooltip'

const Landing = lazy(() => import('@/pages/landing'))

// '/' by default; set when the app is built under a sub-path (vite build --base=/path/)
const BASENAME = import.meta.env.BASE_URL.replace(/\/$/, '') || '/'

export default function App() {
  return (
    <BrowserRouter basename={BASENAME}>
      <TooltipProvider>
        <ToastProvider>
          {/* the curtain sits above the routes so it survives the landing → app switch */}
          <CurtainProvider>
            <Routes>
              <Route
                path="/"
                element={
                  <Suspense fallback={null}>
                    <Landing />
                  </Suspense>
                }
              />
              <Route path="*" element={<AppShell />} />
            </Routes>
          </CurtainProvider>
        </ToastProvider>
      </TooltipProvider>
    </BrowserRouter>
  )
}
