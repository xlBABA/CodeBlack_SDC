import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { useSearchParams } from 'react-router'
import { useToast } from '@/components/ui/toast'
import { STORAGE_PREFIX } from '@/config/product'

const KEY = `${STORAGE_PREFIX}:demo-student`
let lastAnnounced = 0

const stored = () => {
  try {
    return sessionStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

/**
 * Arriving with ?demo=1 (the landing CTA) switches the session to the demo student,
 * says so in a toast, and tidies the URL. Returns whether demo mode is on.
 */
export function useDemoStudent() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const arriving = params.get('demo') === '1'

  useEffect(() => {
    if (!arriving) return
    try {
      sessionStorage.setItem(KEY, '1')
    } catch {
      // storage blocked: demo mode still applies for this page view
    }
    // announce it once the curtain has cleared; not cancelled by the URL clean-up below,
    // and de-duplicated because StrictMode runs this effect twice in development
    if (Date.now() - lastAnnounced > 2000) {
      lastAnnounced = Date.now()
      setTimeout(() => toast('Demo student loaded. Everything here is example data.', { icon: Sparkles }), 900)
    }
    setParams(
      (p) => {
        p.delete('demo')
        return p
      },
      { replace: true },
    )
  }, [arriving, setParams, toast])

  return arriving || stored()
}
