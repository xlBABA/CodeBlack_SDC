// Landing copy and figures in one place so they can be edited without touching layout.
import type { CountFormat } from '@/lib/motion'

/** Boot lines typed by the landing intro. Segments are coloured by kind. */
export type BootSegment = { text: string; kind?: 'prompt' | 'demo' | 'ok' | 'dim' }
export const INTRO_LINES: BootSegment[][] = [
  [{ text: '>', kind: 'prompt' }, { text: ' scanning AI & job-market signals... ' }, { text: '[demo]', kind: 'demo' }],
  [{ text: '>', kind: 'prompt' }, { text: ' mapping skills to future roles... ' }, { text: '30 roles, 8 verified', kind: 'dim' }],
  [{ text: '>', kind: 'prompt' }, { text: ' linking every role to the UN SDGs... ' }, { text: '17 goals', kind: 'dim' }],
  [{ text: '>', kind: 'prompt' }, { text: ' ready', kind: 'ok' }],
]

/** Lines typed while the landing hands you over to the app. */
export const CURTAIN_LINES = {
  demo: [
    [{ text: '>', kind: 'prompt' }, { text: ' loading demo student... ' }, { text: '[fixture]', kind: 'demo' }],
    [{ text: '>', kind: 'prompt' }, { text: ' preparing your overview... ' }, { text: 'ok', kind: 'ok' }],
  ],
  profile: [[{ text: '>', kind: 'prompt' }, { text: ' opening profile builder... ' }, { text: 'ok', kind: 'ok' }]],
} satisfies Record<string, BootSegment[][]>

export const HERO = {
  eyebrow: 'AI career readiness · Malaysian students & fresh graduates',
  // a word wrapped in *stars* is set in the italic serif
  lines: ['Your *future*,', 'mapped for the AI era.'],
  body: 'See which future roles fit the skills you already have, what the market is asking for, and a step-by-step plan to close the gap, linked to the UN SDGs.',
}

/** Read as you scroll: words fill in from faint to full colour. *word* = serif accent. */
export const MANIFESTO =
  'AI is rewriting entry-level work across Malaysia. Some skills are *rising*, some are quietly fading. Mustaqbal reads those signals, lays them over what you already know, and shows you a *path*. Where you go next stays your *choice*.'

export type JourneyStep = { title: string; body: string; kind: 'skills' | 'trends' | 'roles' | 'path' | 'sdg' }
export const JOURNEY: JourneyStep[] = [
  { kind: 'skills', title: 'Your skills, today', body: 'Degree, skills and projects, mapped to one shared vocabulary. Coursework counts.' },
  { kind: 'trends', title: 'Signals, not hype', body: 'Rising and declining skills, each with its source, date and freshness.' },
  { kind: 'roles', title: 'Roles that fit', body: 'Alignment estimates with matched skills, gaps and a caveat beside every score.' },
  { kind: 'path', title: 'A path with hours', body: 'Ordered learning steps and portfolio projects that prove the skill.' },
  { kind: 'sdg', title: 'Impact you can name', body: 'Every role and skill tied to the UN Sustainable Development Goals, with reasons.' },
]

export const CINEMA = {
  intro: 'One profile in. A whole picture out.',
  badges: ['Data analyst', 'Financial analyst', 'Environmental scientist', 'Software developer'],
  title: 'Your alignment report',
  offer: ['Alignment estimates, with caveats', 'Trend signals, with sources', 'A roadmap, with hours', 'SDG links, with reasons'],
}

/**
 * DEMO figures: placeholders for layout only. Every one is labelled DEMO in the UI and
 * will be replaced by cited statistics before the final submission.
 */
export type DemoStat = { value: number; format: CountFormat; label: string }
export const DEMO_STATS: DemoStat[] = [
  { value: 62, format: 'percent', label: 'of sample job ads mention AI tools' },
  { value: 30, format: 'int', label: 'future roles in the catalogue' },
  { value: 120, format: 'hours', label: 'median roadmap to close one gap' },
  { value: 17, format: 'int', label: 'UN SDGs linked to roles & skills' },
]

export const QUOTE = 'AI should widen your options, not narrow them.'
export const FOOTER_LINE = 'Start with today.'
