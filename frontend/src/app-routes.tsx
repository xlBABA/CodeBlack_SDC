import { matchPath } from 'react-router'
import { lazyPage } from '@/lib/lazy-page'

// Pages inside the app shell. Each is its own chunk.
export const APP_ROUTES = [
  { path: '/dashboard', Page: lazyPage(() => import('@/pages/dashboard')) },
  { path: '/start', Page: lazyPage(() => import('@/pages/start')) },
  { path: '/roles', Page: lazyPage(() => import('@/pages/roles')) },
  { path: '/roles/:roleId', Page: lazyPage(() => import('@/pages/role')) },
  { path: '/methodology', Page: lazyPage(() => import('@/pages/methodology')) },
]

export const NotFoundPage = lazyPage(() => import('@/pages/not-found'))

/** Fetches the chunk for whatever page `pathname` resolves to. */
export function preloadRoute(pathname: string): Promise<void> {
  const route = APP_ROUTES.find((r) => matchPath(r.path, pathname))
  return (route?.Page ?? NotFoundPage).preload()
}
