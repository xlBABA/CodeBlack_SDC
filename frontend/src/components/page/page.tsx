import { Children, useLayoutEffect, useRef } from 'react'
import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router'
import { PRODUCT_NAME } from '@/config/product'
import { isAppReady, whenAppReady } from '@/lib/app-ready'
import { gsap } from '@/lib/gsap'
import { enterPage, resetEntered, revealNew } from '@/lib/motion'
import { cn } from '@/lib/utils'
import { CharText } from './char-text'

type Crumb = { label: string; to?: string }

type PageProps = {
  title: string
  /** browser tab title, defaults to the page title */
  docTitle?: string
  crumbs?: Crumb[]
  subtitle?: React.ReactNode
  /** header buttons / stats, right-aligned on desktop */
  actions?: React.ReactNode
  /** extra content under the subtitle (badges, notes) */
  meta?: React.ReactNode
  className?: string
  children: React.ReactNode
}

let firstPage = true

/**
 * Page frame: header plus the entrance choreography. On mount the whole page enters;
 * anything with data-enter that shows up later (data arriving, a tab switching) is picked
 * up by a MutationObserver and gets the shorter reveal.
 */
export function Page({ title, docTitle, crumbs, subtitle, actions, meta, className, children }: PageProps) {
  const root = useRef<HTMLDivElement>(null)

  useLayoutEffect(() => {
    document.title = `${docTitle ?? title} · ${PRODUCT_NAME}`
  }, [title, docTitle])

  useLayoutEffect(() => {
    const el = root.current
    if (!el) return
    const ctx = gsap.context(() => {
      const tl = enterPage(el)
      if (!isAppReady()) {
        tl.pause()
        whenAppReady().then(() => tl.delay(0.12).play())
      }
    }, el)

    let queued = false
    const observer = new MutationObserver((records) => {
      // count-ups rewrite text every frame; only newly added elements matter here
      if (queued || !records.some((r) => Array.from(r.addedNodes).some((n) => n.nodeType === Node.ELEMENT_NODE))) return
      queued = true
      queueMicrotask(() => {
        queued = false
        ctx.add(() => revealNew(el))
      })
    })
    observer.observe(el, { childList: true, subtree: true })

    if (!firstPage) el.querySelector<HTMLElement>('[data-page-title]')?.focus({ preventScroll: true })
    firstPage = false

    return () => {
      observer.disconnect()
      ctx.revert()
      resetEntered(el)
    }
  }, [])

  return (
    <div ref={root} className={cn('pb-10', className)}>
      <header className="mb-5 grid items-end gap-x-6 gap-y-4 md:grid-cols-[minmax(0,1fr)_auto]">
        <div className="min-w-0">
          {crumbs && crumbs.length > 0 && (
            <nav aria-label="Breadcrumb" data-enter="head" className="mb-1.5">
              <ol className="flex flex-wrap items-center gap-1.5 text-sm font-semibold text-muted-foreground">
                {crumbs.map((c, i) => (
                  <li key={i} className="flex items-center gap-1.5">
                    {i > 0 && <ChevronRight className="size-3.5 text-faint" aria-hidden />}
                    {c.to ? (
                      <Link to={c.to} className="rounded-sm hover:text-foreground hover:underline">
                        {c.label}
                      </Link>
                    ) : (
                      <span aria-current="page" className="text-foreground">
                        {c.label}
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            </nav>
          )}
          <h1
            data-page-title
            tabIndex={-1}
            className="text-[clamp(1.75rem,1.2rem+1.7vw,2.55rem)] leading-[1.1] font-extrabold tracking-[-0.025em]"
          >
            <CharText text={title} />
          </h1>
          {subtitle && (
            <p data-enter="head" className="mt-2 max-w-[62ch] text-lg text-muted-foreground">
              {subtitle}
            </p>
          )}
          {meta && (
            <div data-enter="head" className="mt-3 flex flex-wrap items-center gap-2">
              {meta}
            </div>
          )}
        </div>
        {actions && (
          <div className="flex flex-wrap items-center gap-2.5">
            {Children.toArray(actions).map((action, i) => (
              // wrapper takes the entrance so a magnetic button inside keeps its own transform
              <div key={i} data-enter="action">
                {action}
              </div>
            ))}
          </div>
        )}
      </header>
      {children}
    </div>
  )
}
