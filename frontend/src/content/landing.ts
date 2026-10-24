// Landing copy and figures in one place so they can be edited without touching layout.
import type { CountFormat } from '@/lib/motion'
import { catalogResources, catalogRoles } from './catalog'

/** One run of a boot line, coloured by kind. */
export type BootSegment = { text: string; kind?: 'prompt' | 'demo' | 'ok' | 'dim' }

/** Lines typed while the landing hands you over to the app. */
export const CURTAIN_LINES = {
  demo: [
    [{ text: '>', kind: 'prompt' }, { text: ' loading demo student... ' }, { text: '[fixture]', kind: 'demo' }],
    [{ text: '>', kind: 'prompt' }, { text: ' preparing your dashboard... ' }, { text: 'ok', kind: 'ok' }],
  ],
  profile: [[{ text: '>', kind: 'prompt' }, { text: ' opening profile builder... ' }, { text: 'ok', kind: 'ok' }]],
  dashboard: [[{ text: '>', kind: 'prompt' }, { text: ' opening your dashboard... ' }, { text: 'ok', kind: 'ok' }]],
} satisfies Record<string, BootSegment[][]>

export const HERO = {
  eyebrow: 'Career planning for Malaysian students and fresh graduates',
  // a word wrapped in *stars* is set in the italic serif
  lines: ['Your *future*,', 'mapped for the AI era.'],
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

/** Real catalogue entries (roles.json, resources.json) shown on the landing page, labelled "Example". */
export const EXAMPLE_LABEL = 'Example'
export const EXAMPLE_ROLES = catalogRoles(['data_analyst', 'financial_analyst', 'environmental_scientist', 'software_developer'])
export const EXAMPLE_PATH = catalogResources(['mslearn_tsql_query_modify', 'mslearn_power_bi_prepare_visualize', 'mslearn_python_part1_fundamentals'])

export const CINEMA = {
  intro: 'One profile. Every role compared.',
  badges: EXAMPLE_ROLES.map((r) => r.role_title),
  title: 'Your alignment report',
  offer: ['Alignment estimates, with caveats', 'GitHub activity signals, with sources', 'A roadmap, with hours', 'SDG links, with reasons'],
}

const HAYS = 'https://sea.peoplemattersglobal.com/article/strategic-hr/ai-in-malaysian-workplaces-a-strategic-outlook-46436'

/** Published figures, each shown with its source; the last is our own SDG scope. */
export type Stat = { value: number; format: CountFormat; label: string; source: string; href: string }
export const STATS: Stat[] = [
  { value: 56, format: 'percent', label: 'of professionals in Malaysia already use AI tools at work', source: 'Hays Asia Salary Guide 2025', href: HAYS },
  { value: 26, format: 'percent', label: 'have received any formal AI training', source: 'Hays Asia Salary Guide 2025', href: HAYS },
  {
    value: 600_000,
    format: 'plus',
    label: 'workers in Malaysia must reskill within three to five years',
    source: 'Ministry of Science, Technology and Innovation, Jan 2025',
    href: 'https://www.malaymail.com/news/malaysia/2025/01/07/mosti-ai-disruption-looms-in-malaysia-600000-workers-must-reskill-in-three-to-five-years/162368',
  },
  {
    value: 39,
    format: 'percent',
    label: 'of key skills in the job market are expected to change by 2030',
    source: 'World Economic Forum, Future of Jobs Report 2025',
    href: 'https://www.weforum.org/stories/2025/01/future-of-jobs-report-2025-jobs-of-the-future-and-the-skills-you-need-to-get-them',
  },
  { value: 5, format: 'int', label: 'UN Sustainable Development Goals this tool is built around', source: 'Goals 4, 8, 9, 5 and 10 · United Nations', href: SDG_SOURCE },
]

export const QUOTE = 'AI should widen your options, not narrow them.'
export const FOOTER_LINE = 'Start with today.'
