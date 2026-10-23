// Landing copy and figures in one place so they can be edited without touching layout.
import type { CountFormat } from '@/lib/motion'

/** One run of a boot line, coloured by kind. */
export type BootSegment = { text: string; kind?: 'prompt' | 'demo' | 'ok' | 'dim' }

/** Lines typed while the landing hands you over to the app. */
export const CURTAIN_LINES = {
  demo: [
    [{ text: '>', kind: 'prompt' }, { text: ' loading demo student... ' }, { text: '[fixture]', kind: 'demo' }],
    [{ text: '>', kind: 'prompt' }, { text: ' preparing your overview... ' }, { text: 'ok', kind: 'ok' }],
  ],
  profile: [[{ text: '>', kind: 'prompt' }, { text: ' opening profile builder... ' }, { text: 'ok', kind: 'ok' }]],
  dashboard: [[{ text: '>', kind: 'prompt' }, { text: ' opening your dashboard... ' }, { text: 'ok', kind: 'ok' }]],
} satisfies Record<string, BootSegment[][]>

export const HERO = {
  eyebrow: 'Career planning for Malaysian students and fresh graduates',
  // a word wrapped in *stars* is set in the italic serif
  lines: ['Your *future*,', 'mapped from today.'],
  body: 'See which roles fit the skills you have now, how GitHub developer activity is moving for those skills, and what to learn next, with hours for each step.',
}

/** Read as you scroll: words fill in from faint to full colour. *word* = serif accent. */
export const MANIFESTO =
  'Entry-level jobs are changing as AI tools spread. Mustaqbal compares your skills with what each role needs, adds dated GitHub activity for those skills, and gives you a *path* with hours. The *choice* stays yours.'

export type JourneyStep = { title: string; body: string; kind: 'skills' | 'trends' | 'roles' | 'path' | 'sdg' }
export const JOURNEY: JourneyStep[] = [
  { kind: 'skills', title: 'Your skills, today', body: 'Your degree, skills and projects, matched to the same 20-skill list every role uses. Coursework counts.' },
  { kind: 'trends', title: 'Dated signals', body: 'How many new GitHub projects use each skill, with the source and dates. Developer activity, not job demand.' },
  { kind: 'roles', title: 'Roles that fit', body: 'Alignment estimates with matched skills, gaps and a caveat beside every score.' },
  { kind: 'path', title: 'A path with hours', body: 'Learning steps in order, with hours, and projects that show the skill.' },
  { kind: 'sdg', title: 'Impact you can name', body: 'Built for UN Goal 4, Quality Education, and four goals that depend on it.' },
]

/** The SDGs of our domain (Aiversecity, Future-Ready Workforce). Icons are the official UN web set in public/sdg. */
export type DomainSdg = { goal: number; name: string; line: string }
export const DOMAIN_SDGS: { main: DomainSdg; related: DomainSdg[] } = {
  main: { goal: 4, name: 'Quality Education', line: 'Skills for decent jobs (target 4.4) and lifelong learning (4.3), through personal reskilling paths built from free or low-cost courses.' },
  related: [
    { goal: 8, name: 'Decent Work and Economic Growth', line: 'Matches students to future-ready roles (targets 8.2, 8.5).' },
    { goal: 9, name: 'Industry, Innovation and Infrastructure', line: 'Skills for technology- and AI-driven industries.' },
    { goal: 5, name: 'Gender Equality', line: 'Matching never asks for or uses gender.' },
    { goal: 10, name: 'Reduced Inequalities', line: 'Ranking never uses age or family background. Courses are free or low-cost.' },
  ],
}
export const SDG_SOURCE = 'https://www.un.org/sustainabledevelopment'
export const UN_DISCLAIMER =
  'The content of this publication has not been approved by the United Nations and does not reflect the views of the United Nations or its officials or Member States.'

export const CINEMA = {
  intro: 'One profile. Every role compared.',
  badges: ['Data analyst', 'Financial analyst', 'Environmental scientist', 'Software developer'],
  title: 'Your alignment report',
  offer: ['Alignment estimates, with caveats', 'GitHub activity signals, with sources', 'A roadmap, with hours', 'SDG links, with reasons'],
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
