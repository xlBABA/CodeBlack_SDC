import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { useSearchParams } from 'react-router'
import { useToast } from '@/components/ui/toast'
import { useRequest } from '@/hooks/use-request'
import { loadDemoProfile } from '@/lib/profile-store'

/**
 * Arriving with ?demo=1 (the landing CTAs) analyses the synthetic demo student through the
 * real API, stores it as the current profile, says so, and tidies the URL.
 */
export function useDemoStudent() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const arriving = params.get('demo') === '1'
  const [state, retry] = useRequest(arriving ? 'demo-profile' : null, (signal) => loadDemoProfile(signal))

  useEffect(() => {
    if (!arriving || state.status !== 'ok') return
    toast('Demo student loaded. Everything about them is synthetic.', { icon: Sparkles })
    setParams(
      (p) => {
        p.delete('demo')
        return p
      },
      { replace: true },
    )
  }, [arriving, state.status, setParams, toast])

  return { loading: arriving && state.status === 'loading', error: arriving && state.status === 'error' ? state.error : null, retry }
}
