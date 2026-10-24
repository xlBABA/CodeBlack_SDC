import { useId } from 'react'
import { PRODUCT_NAME, PRODUCT_SHORT } from '@/config/product'
import { cn } from '@/lib/utils'

/**
 * Mustaqbal AI mark: an "M" drawn as one rising line, from today (bottom left) up to a
 * glowing node (the future). The node is butter yellow in every theme.
 */
export function BrandMark({ className, flat = false }: { className?: string; flat?: boolean }) {
  // unique per instance: a gradient referenced from a hidden SVG stops rendering in Chrome
  const gradient = `mq-tile-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
  return (
    <svg viewBox="0 0 48 48" aria-hidden className={cn('size-10 flex-none', className)}>
      {!flat && (
        <>
          <defs>
            <linearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="var(--primary)" />
              <stop offset="1" stopColor="var(--primary-2)" />
            </linearGradient>
          </defs>
          <rect width="48" height="48" rx="14" fill={`url(#${gradient})`} />
          <rect x="0.75" y="0.75" width="46.5" height="46.5" rx="13.25" fill="none" stroke="#ffffff" strokeOpacity=".18" strokeWidth="1.5" />
        </>
      )}
      <path
        d="M12.5 35V16.5L24 28l9.5-9.5"
        fill="none"
        stroke={flat ? 'currentColor' : '#f8f5ef'}
        strokeWidth="4.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="36.5" cy="14.5" r="7" fill="var(--node)" opacity=".25" />
      <circle cx="36.5" cy="14.5" r="3.8" fill="var(--node)" />
    </svg>
  )
}

/** Wordmark built from PRODUCT_NAME: a trailing "AI" becomes a small pill. */
export function Wordmark({ className }: { className?: string }) {
  const parts = PRODUCT_NAME.split(' ')
  const hasAi = parts.at(-1) === 'AI'
  const base = hasAi ? parts.slice(0, -1).join(' ') : PRODUCT_NAME
  return (
    <span className={cn('inline-flex items-center gap-1.5 leading-none', className)} aria-label={PRODUCT_NAME}>
      <b aria-hidden className="text-[1.3em] font-extrabold tracking-[-0.035em] lowercase">
        {base}
      </b>
      {hasAi && (
        <span aria-hidden className="rounded-full bg-primary px-1.5 py-[3px] text-[0.62em] font-extrabold tracking-[0.04em] text-primary-foreground">
          AI
        </span>
      )}
    </span>
  )
}

export function Brand({ compact = false, tagline = false }: { compact?: boolean; tagline?: boolean }) {
  return (
    <span className="flex min-w-0 items-center gap-2.5">
      <BrandMark />
      {!compact && (
        <span className="grid min-w-0 gap-1">
          <Wordmark className="text-base" />
          {tagline && <small className="truncate text-xs font-semibold text-muted-foreground">{PRODUCT_SHORT}</small>}
        </span>
      )}
    </span>
  )
}
