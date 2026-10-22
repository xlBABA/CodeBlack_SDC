import type { JourneyStep } from '@/content/landing'

// Small illustrative "screens" for each journey step. Static demo content.

function Skills() {
  const rows: [string, number][] = [['Excel', 3], ['Python', 2], ['Statistics', 2], ['SQL', 1], ['Communication', 3]]
  return (
    <ul className="grid gap-2">
      {rows.map(([s, lvl]) => (
        <li key={s} className="flex items-center justify-between rounded-full bg-raised px-4 py-2.5 shadow-card">
          <b>{s}</b>
          <span className="flex gap-1" aria-label={`level ${lvl} of 3`}>
            {[1, 2, 3].map((n) => (
              <i key={n} className={n <= lvl ? 'size-2.5 rounded-full bg-primary' : 'size-2.5 rounded-full bg-well'} />
            ))}
          </span>
        </li>
      ))}
    </ul>
  )
}
function Trends() {
  const rows: [string, number, boolean][] = [['AI literacy', 41, false], ['ESG reporting', 27, true], ['SQL', 18, false], ['Manual data entry', -33, true]]
  return (
    <ul className="grid gap-3">
      {rows.map(([s, v, stale]) => (
        <li key={s}>
          <div className="flex justify-between text-sm font-semibold">
            <span>{s}</span>
            <span className={v > 0 ? 'text-good' : 'text-tomato'}>{v > 0 ? `+${v}` : v}%</span>
          </div>
          <div className="relative mt-1 h-2.5 rounded-full bg-well">
            <i
              className={`absolute inset-y-0 rounded-full ${stale ? 'hatch' : v > 0 ? 'bg-good' : 'bg-tomato'}`}
              style={v > 0 ? { left: '50%', width: `${(v / 41) * 50}%` } : { right: '50%', width: `${(-v / 41) * 50}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}
function Roles() {
  const tiles: [string, number, string][] = [
    ['Data analyst', 76, 'bg-ink text-ink-foreground'],
    ['Financial analyst', 65, 'bg-primary text-primary-foreground'],
    ['Sustainability coordinator', 59, 'bg-tomato text-tomato-foreground'],
    ['Mechanical design engineer', 40, 'bg-butter text-butter-foreground'],
  ]
  return (
    <div className="grid grid-cols-2 gap-2.5">
      {tiles.map(([t, n, cls]) => (
        <div key={t} className={`flex min-h-[110px] flex-col justify-between rounded-[18px] p-3 ${cls}`}>
          <b className="text-sm leading-tight">{t}</b>
          <span>
            <b className="text-2xl">{n}</b> <small className="text-2xs opacity-80">alignment estimate</small>
          </span>
        </div>
      ))}
    </div>
  )
}
function Path() {
  const steps: [string, string][] = [['SQL joins & aggregation', '20 h'], ['Dashboard project', '30 h'], ['Data storytelling', '12 h']]
  return (
    <ol className="grid">
      {steps.map(([t, h], i) => (
        <li key={t} className="relative grid pt-5 first:pt-0">
          {i > 0 && <span aria-hidden className="absolute top-0 left-1/2 h-5 border-l-2 border-dotted border-line-2" />}
          <div className="flex items-center justify-between rounded-[16px] border border-rim bg-raised px-4 py-3 shadow-card dark:border-line">
            <b>{t}</b>
            <span className="rounded-full bg-well px-2 py-0.5 text-sm font-semibold">{h}</span>
          </div>
        </li>
      ))}
    </ol>
  )
}
function Sdg() {
  return (
    <div className="grid grid-cols-6 gap-1.5">
      {Array.from({ length: 17 }, (_, i) => (
        <span key={i} className="grid aspect-square place-items-center rounded-[10px] text-sm font-extrabold text-white" style={{ background: `var(--sdg-${i + 1})` }}>
          {i + 1}
        </span>
      ))}
    </div>
  )
}

export function JourneyArt({ kind }: { kind: JourneyStep['kind'] }) {
  return { skills: <Skills />, trends: <Trends />, roles: <Roles />, path: <Path />, sdg: <Sdg /> }[kind]
}
