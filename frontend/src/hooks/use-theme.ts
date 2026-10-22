import { useSyncExternalStore } from 'react'
import { currentAccent, currentTheme, setAccent, setTheme, subscribe } from '@/lib/theme'

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, currentTheme)
  const accent = useSyncExternalStore(subscribe, currentAccent)
  return { theme, accent, setTheme, setAccent }
}
