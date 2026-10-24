import { SdgIcon } from '@/components/sdg-icon'
import { formatHours } from '@/content/catalog'
import { DOMAIN_SDGS, EXAMPLE_LABEL, EXAMPLE_PATH, EXAMPLE_ROLES, type JourneyStep } from '@/content/landing'
import { skillName } from '@/content/skills'

// Small illustrative "screens" for each journey step, built from real catalogue entries.

function ExampleTag() {
  return <p className="mb-2 text-xs font-semibold text-muted-foreground">{EXAMPLE_LABEL}</p>
}

function Skills() {
  // real catalogue skills; the self-rated levels (1-3) are illustrative
  const rows: [string, number][] = [['excel', 3], ['python', 2], ['sql', 1], ['data_visualization', 2], ['mathematics', 3]]
  return (
    <div>
      <ExampleTag />
      <ul className="grid gap-2">
      {rows.map(([s, lvl]) => (
        <li key={s} className="flex items-center justify-between rounded-full bg-raised px-4 py-2.5 shadow-card">
          <b>{skillName(s)}</b>
          <span className="flex gap-1" aria-label={`level ${lvl} of 3`}>
            {[1, 2, 3].map((n) => (
              <i key={n} className={n <= lvl ? 'size-2.5 rounded-full bg-primary' : 'size-2.5 rounded-full bg-well'} />
            ))}
          </span>
        </li>
      ))}
      </ul>
    </div>
  )
}
// Change in new GitHub repositories per topic, last 30 days vs the 30 before, from the team's
// cached snapshots (data/trend_snapshots, retrieved 21 Oct 2026).
const TREND_ROWS: [string, number][] = [['MATLAB', 51.5], ['Python', 15.8], ['SQL', 7.9], ['Financial analysis software', -6.1]]
const TREND_MAX = Math.max(...TREND_ROWS.map(([, v]) => Math.abs(v)))

function Trends() {
  return (
    <div className="grid gap-3">
      <ul className="grid gap-3">
        {TREND_ROWS.map(([s, v]) => (
          <li key={s}>
            <div className="flex justify-between text-sm font-semibold">
              <span>{s}</span>
              <span className={v > 0 ? 'text-good' : 'text-tomato'}>{v > 0 ? `+${v}` : v}%</span>
            </div>
            <div className="relative mt-1 h-2.5 rounded-full bg-well">
              <i
                className={`absolute inset-y-0 rounded-full ${v > 0 ? 'bg-good' : 'bg-tomato'}`}
                style={v > 0 ? { left: '50%', width: `${(v / TREND_MAX) * 50}%` } : { right: '50%', width: `${(-v / TREND_MAX) * 50}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">New GitHub repositories, last 30 days vs the 30 before. Cached 21 Oct 2026. Developer activity, not job demand.</p>
    </div>
  )
}
const TILE_COLORS = ['bg-ink text-ink-foreground', 'bg-primary text-primary-foreground', 'bg-tomato text-tomato-foreground', 'bg-butter text-butter-foreground']

function Roles() {
  return (
    <div>
      <ExampleTag />
      <div className="grid grid-cols-2 gap-2.5">
        {EXAMPLE_ROLES.map((role, i) => (
          <div key={role.role_id} className={`flex min-h-[110px] flex-col justify-between rounded-[18px] p-3 ${TILE_COLORS[i % TILE_COLORS.length]}`}>
            <b className="text-sm leading-tight">{role.role_title}</b>
            <span className="text-xs opacity-85">
              O*NET {role.onet_soc_code}
              <br />
              {role.core_skills} core skills
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
function Path() {
  return (
    <div>
      <ExampleTag />
      <ol className="grid grid-cols-1">
        {EXAMPLE_PATH.map((step, i) => (
          <li key={step.resource_id} className="relative grid grid-cols-1 pt-5 first:pt-0">
            {i > 0 && <span aria-hidden className="absolute top-0 left-1/2 h-5 border-l-2 border-dotted border-line-2" />}
            <div className="flex items-center justify-between gap-3 rounded-[16px] border border-rim bg-raised px-4 py-3 shadow-card dark:border-line">
              <span className="min-w-0">
                <b className="block truncate">{step.title}</b>
                <small className="text-xs text-muted-foreground">
                  {step.provider}
                  {step.provider_stated ? '' : ' · team estimate'}
                </small>
              </span>
              <span className="flex-none rounded-full bg-well px-2 py-0.5 text-sm font-semibold">{formatHours(step.hours)}</span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
function Sdg() {
  const { main, related } = DOMAIN_SDGS
  return (
    <div className="grid gap-2 md:gap-3">
      <div className="flex items-center gap-3 rounded-[16px] bg-raised p-2 pr-3 shadow-card md:p-2.5">
        <SdgIcon sdg={main} className="size-12 md:size-[clamp(56px,7svh,80px)]" />
        <p className="text-xs leading-snug md:text-sm">
          <b className="block text-2xs font-bold tracking-[0.1em] text-primary uppercase">Main goal</b>
          {main.line}
        </p>
      </div>
      <ul className="grid gap-y-2 md:grid-cols-2 md:gap-x-3 md:gap-y-2.5">
        {related.map((g) => (
          <li key={g.goal} className="flex items-start gap-2">
            <SdgIcon sdg={g} className="size-8 md:size-[clamp(36px,5svh,48px)]" />
            <span className="text-[0.6875rem] leading-snug md:text-xs">{g.line}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function JourneyArt({ kind }: { kind: JourneyStep['kind'] }) {
  return { skills: <Skills />, trends: <Trends />, roles: <Roles />, path: <Path />, sdg: <Sdg /> }[kind]
}
