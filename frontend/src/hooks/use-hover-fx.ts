import { useEffect, type RefObject } from 'react'
import { gsap } from '@/lib/gsap'
import { canHover, prefersReducedMotion } from '@/lib/motion'

/** Element drifts toward the pointer (×.24 / ×.30 of the offset) and springs back. */
export function useMagnetic(ref: RefObject<HTMLElement | null>, enabled = true) {
  useEffect(() => {
    const el = ref.current
    if (!el || !enabled || !canHover()) return
    const toX = gsap.quickTo(el, 'x', { duration: 0.5, ease: 'power3.out' })
    const toY = gsap.quickTo(el, 'y', { duration: 0.5, ease: 'power3.out' })
    const move = (e: PointerEvent) => {
      if (prefersReducedMotion()) return
      const r = el.getBoundingClientRect()
      toX((e.clientX - r.left - r.width / 2) * 0.24)
      toY((e.clientY - r.top - r.height / 2) * 0.3)
    }
    const leave = () => {
      toX(0)
      toY(0)
    }
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerleave', leave)
    return () => {
      el.removeEventListener('pointermove', move)
      el.removeEventListener('pointerleave', leave)
      gsap.set(el, { clearProps: 'x,y' })
    }
  }, [ref, enabled])
}

/** Card rises 4px under the pointer. Waits for its entrance tween so the two never fight. */
export function useLift(ref: RefObject<HTMLElement | null>, enabled = true, distance = -4) {
  useEffect(() => {
    const el = ref.current
    if (!el || !enabled || !canHover()) return
    const enter = () => {
      if (prefersReducedMotion() || gsap.isTweening(el)) return
      gsap.to(el, { y: distance, duration: 0.45, ease: 'power3.out', overwrite: 'auto' })
    }
    const leave = () => {
      if (gsap.getProperty(el, 'y') === 0) return
      gsap.to(el, { y: 0, duration: 0.5, ease: 'power3.out', overwrite: 'auto', clearProps: 'transform' })
    }
    el.addEventListener('pointerenter', enter)
    el.addEventListener('pointerleave', leave)
    return () => {
      el.removeEventListener('pointerenter', enter)
      el.removeEventListener('pointerleave', leave)
    }
  }, [ref, enabled, distance])
}
