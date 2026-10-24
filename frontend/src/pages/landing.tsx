import { useCallback, useEffect, useLayoutEffect, useState } from 'react'
import { Cinema } from '@/components/landing/cinema'
import { FooterCta } from '@/components/landing/footer-cta'
import { HeroWindow } from '@/components/landing/hero-window'
import { Journey } from '@/components/landing/journey'
import { LandingHeader } from '@/components/landing/landing-header'
import { LandingIntro } from '@/components/landing/landing-intro'
import { Manifesto } from '@/components/landing/manifesto'
import { Numbers } from '@/components/landing/numbers'
import { Quote } from '@/components/landing/quote'
import { Mesh } from '@/components/mesh'
import { PRODUCT_NAME, PRODUCT_TAGLINE, STORAGE_PREFIX } from '@/config/product'
import { ScrollTrigger } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { useSmoothScroll } from '@/lib/smooth-scroll'

const INTRO_KEY = `${STORAGE_PREFIX}:intro-seen`

function introAlreadySeen() {
  try {
    return sessionStorage.getItem(INTRO_KEY) === '1'
  } catch {
    return false
  }
}

type IntroState = 'playing' | 'lifting' | 'done'

/**
 * Landing: boot intro, then a clip-reveal hero, a scroll-filled manifesto,
 * a horizontal journey, the "cinema" report reveal, demo numbers, a quote and the footer CTA.
 */
export default function Landing() {
  const lenis = useSmoothScroll()
  const [intro, setIntro] = useState<IntroState>(() => (prefersReducedMotion() || introAlreadySeen() ? 'done' : 'playing'))
  const ready = intro !== 'playing'

  useLayoutEffect(() => {
    document.title = `${PRODUCT_NAME} — ${PRODUCT_TAGLINE}`
    window.scrollTo(0, 0)
  }, [])

  // keep the page still while the intro covers it
  useEffect(() => {
    if (intro === 'done') return
    const html = document.documentElement
    const smooth = lenis.current
    html.style.overflow = 'hidden'
    smooth?.stop()
    return () => {
      html.style.overflow = ''
      smooth?.start()
      ScrollTrigger.refresh()
    }
  }, [intro, lenis])

  const onLift = useCallback(() => setIntro('lifting'), [])
  const onDone = useCallback(() => {
    try {
      sessionStorage.setItem(INTRO_KEY, '1')
    } catch {
      // storage blocked: the intro will just play again next time
    }
    setIntro('done')
  }, [])

  return (
    <>
      {intro !== 'done' && <LandingIntro onLift={onLift} onDone={onDone} />}
      <Mesh />
      <LandingHeader ready={ready} lenis={lenis} />
      <main id="main">
        <HeroWindow ready={ready} />
        <Manifesto />
        <Journey />
        <Cinema />
        <Numbers />
        <Quote />
      </main>
      <FooterCta />
    </>
  )
}
