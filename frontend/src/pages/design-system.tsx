import { useRef, useState } from 'react'
import { Bell, Copy, Moon, Palette, Play, RotateCcw, Sparkles, Zap } from 'lucide-react'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Page } from '@/components/page/page'
import { CountUp } from '@/components/page/count-up'
import { AccentPicker } from '@/components/accent-picker'
import { ThemeToggle } from '@/components/theme-toggle'
import { Badge, type Tone } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader } from '@/components/ui/card'
import { IconButton } from '@/components/ui/icon-button'
import { ProgressRing } from '@/components/ui/progress-ring'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { flashValue } from '@/lib/motion'

const SURFACES = ['bg', 'glass', 'solid', 'raised', 'well', 'primary', 'ink', 'butter']
const TONES: Tone[] = ['primary', 'emerald', 'tomato', 'butter', 'sky', 'plum', 'teal', 'slate', 'good', 'warn', 'bad', 'faint']
// sample values for demonstrating the components only; never shown as real results
const SAMPLE = { ring: 72, bars: [0.86, 0.6, 0.38], counts: [1240, 64, 17] }

/** Living reference for the design tokens and motion. Not linked from the nav; open /design. */
export default function DesignSystem() {
  const toast = useToast()
  const [replay, setReplay] = useState(0)
  const [n, setN] = useState(3)
  const flashRef = useRef<HTMLElement>(null)

  return (
    <Page
      title="Design system"
      crumbs={[{ label: 'Prototype' }, { label: 'Design' }]}
      subtitle="Tokens, components and motion in one place. Flip the theme to check both palettes."
      meta={
        <>
          <DataModeBadge mode="fixture" />
          <DataModeBadge mode="cached" />
          <DataModeBadge mode="live" />
        </>
      }
      actions={[
        <ThemeToggle key="t" />,
        <div key="a" className="rounded-full bg-ink text-ink-foreground">
          <AccentPicker side="top" />
        </div>,
        <Button key="r" variant="secondary" onClick={() => setReplay((r) => r + 1)}>
          <RotateCcw />
          Replay entrance
        </Button>,
      ]}
    >
      <div key={replay} className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader icon={Palette} title="Surfaces" />
          <div className="grid grid-cols-4 gap-2.5">
            {SURFACES.map((s) => (
              <div key={s} data-enter="item" className="grid gap-1.5">
                <span className="h-14 rounded-tile border border-line" style={{ background: `var(--${s})` }} />
                <code className="font-mono text-2xs text-muted-foreground">--{s}</code>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader icon={Sparkles} title="Tones" />
          <div className="flex flex-wrap gap-2">
            {TONES.map((t) => (
              <Badge key={t} tone={t} dot>
                {t}
              </Badge>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-[repeat(17,minmax(0,1fr))] gap-1" aria-label="The 17 UN SDG colours">
            {Array.from({ length: 17 }, (_, i) => (
              <span key={i} data-enter="pop" title={`SDG ${i + 1}`} className="aspect-square rounded-md" style={{ background: `var(--sdg-${i + 1})` }} />
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader icon={Zap} title="Buttons" />
          <div className="flex flex-wrap items-center gap-2.5">
            <Button magnetic>Primary (magnetic)</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ink">Ink</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="link">Link</Button>
            <Button size="sm">Small</Button>
            <Button disabled>Disabled</Button>
          </div>
          <div className="mt-4 flex items-center gap-2.5">
            <IconButton variant="glass" label="Notifications">
              <Bell />
            </IconButton>
            <IconButton label="Copy">
              <Copy />
            </IconButton>
            <IconButton variant="ghost" label="Dark mode">
              <Moon />
            </IconButton>
          </div>
        </Card>

        <Card lift>
          <CardHeader icon={Play} title="Motion" action={<Badge tone="warn">sample values</Badge>} />
          <div className="flex flex-wrap items-center gap-6">
            <ProgressRing value={SAMPLE.ring} caption="alignment estimate" tone="var(--primary)" />
            <div className="grid flex-1 gap-3">
              {SAMPLE.bars.map((b, i) => (
                <div key={i} className="h-2.5 overflow-hidden rounded-full bg-well">
                  <i data-enter="bar" className="block h-full rounded-full bg-primary" style={{ width: `${b * 100}%` }} />
                </div>
              ))}
            </div>
          </div>
          <div className="mt-5 grid grid-cols-3 gap-2.5">
            {SAMPLE.counts.map((c, i) => (
              <div key={i} data-enter="item" className="rounded-tile bg-surface-2 p-3">
                <CountUp value={c} className="text-2xl font-extrabold" />
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Feedback" icon={Bell} />
          <div className="flex flex-wrap items-center gap-2.5">
            <Button variant="secondary" onClick={() => toast('Profile saved')}>
              Toast
            </Button>
            <Button variant="secondary" onClick={() => toast('Skill removed', { undo: () => toast('Skill restored') })}>
              Toast with undo
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setN((v) => v + 1)
                if (flashRef.current) flashValue(flashRef.current)
              }}
            >
              Flash value
            </Button>
            <b ref={flashRef} className="inline-block text-2xl tabular-nums">
              {n}
            </b>
          </div>
        </Card>

        <Card>
          <CardHeader title="Loading" />
          <div className="grid gap-2.5">
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-5/6" />
            <div className="flex gap-2.5">
              <Skeleton className="h-16 flex-1 rounded-tile" />
              <Skeleton className="h-16 flex-1 rounded-tile" />
            </div>
          </div>
        </Card>
      </div>
    </Page>
  )
}
