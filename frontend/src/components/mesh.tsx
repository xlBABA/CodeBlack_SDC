import { useRef } from 'react'
import { gsap, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'

/**
 * Background of three large blurred blobs that drift slowly forever (Rapport idea:
 * 14 s + 4 s per blob, sine yoyo). Colours come from --mesh-a/b/c, so they follow the theme.
 */
export function Mesh() {
  const root = useRef<HTMLDivElement>(null)
  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      gsap.utils.toArray<HTMLElement>('i', root.current).forEach((blob, i) => {
        gsap.to(blob, { x: [60, -50, 40][i], y: [40, -60, 50][i], scale: [1.08, 0.94, 1.1][i], duration: 14 + i * 4, ease: 'sine.inOut', yoyo: true, repeat: -1 })
      })
    },
    { scope: root },
  )
  return (
    <div ref={root} data-mesh aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <i className="absolute -top-[24vmax] -left-[18vmax] size-[62vmax] rounded-full bg-[radial-gradient(closest-side,var(--mesh-a),transparent)] blur-[60px]" />
      <i className="absolute -right-[24vmax] -bottom-[30vmax] size-[70vmax] rounded-full bg-[radial-gradient(closest-side,var(--mesh-b),transparent)] blur-[60px]" />
      <i className="absolute -top-[14vmax] left-[38vw] size-[46vmax] rounded-full bg-[radial-gradient(closest-side,var(--mesh-c),transparent)] blur-[60px]" />
    </div>
  )
}
