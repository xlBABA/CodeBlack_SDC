import { Ban, Calculator, Database, Scale } from 'lucide-react'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Page } from '@/components/page/page'
import { Card, CardHeader } from '@/components/ui/card'

const PARTS = [
  ['Skills', 'How many of the role’s core skills you reported, weighted by how central each one is.'],
  ['Experience', 'Whether your projects and experience mention skills the role needs.'],
  ['Prerequisites', 'Whether you meet the role’s hard prerequisites, such as a level of study.'],
  ['Transferable', 'Skills from coursework and projects that carry over to the role.'],
]

/** How the numbers are made and what they are not. Plain copy; nothing here is fetched. */
export default function Methodology() {
  return (
    <Page
      title="How it works"
      crumbs={[{ label: 'Understand' }, { label: 'Methodology' }]}
      subtitle="What the alignment estimate measures, where data comes from and what the system does not do."
    >
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader icon={Calculator} title="The alignment estimate" />
          <p data-enter="item" className="text-muted-foreground">
            A 0 to 100 score for how closely the skills you reported line up with a role’s core skills. It is calculated by a deterministic matching service, so the same profile always gets the same score, and it
            is built from four parts:
          </p>
          <dl className="mt-3 grid gap-2">
            {PARTS.map(([k, v]) => (
              <div key={k} data-enter="item" className="rounded-[14px] bg-well px-3 py-2">
                <dt className="font-semibold">{k}</dt>
                <dd className="text-sm text-muted-foreground">{v}</dd>
              </div>
            ))}
          </dl>
          <p data-enter="item" className="mt-3 text-sm text-muted-foreground">
            The method is an initial team choice, not a validated model. Every score is shown with at least one caveat.
          </p>
        </Card>

        <Card>
          <CardHeader icon={Database} title="Live, cached and demo data" />
          <ul className="grid gap-3">
            {(
              [
                ['live', 'Calculated just now from your profile.'],
                ['cached', 'Taken from a verified dataset the team saved earlier, such as the SDG links.'],
                ['fixture', 'Produced by the prototype’s fixed example logic or placeholder data. Treat it as an illustration.'],
              ] as const
            ).map(([mode, text]) => (
              <li key={mode} data-enter="item" className="flex items-start gap-3">
                <DataModeBadge mode={mode} className="mt-0.5 flex-none" />
                <span className="text-muted-foreground">{text}</span>
              </li>
            ))}
          </ul>
          <p data-enter="item" className="mt-3 text-sm text-muted-foreground">
            Every card says which kind of data it shows, and the notes under it repeat what the service said about its sources. When data is missing we show an empty state instead of filling the gap.
          </p>
        </Card>

        <Card>
          <CardHeader icon={Ban} title="What it does not do" />
          <ul className="grid gap-2 text-muted-foreground">
            {[
              'It does not predict whether you will be hired, admitted or paid a certain amount.',
              'It does not decide for you. Scores and roadmaps are prompts to think with.',
              'Scenarios are illustrations of change, not labour-market forecasts.',
              'Project simulations assume you gained the skills; they do not measure real outcomes.',
            ].map((t) => (
              <li key={t} data-enter="item" className="rounded-[14px] bg-well px-3 py-2">
                {t}
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardHeader icon={Scale} title="Fairness" />
          <p data-enter="item" className="text-muted-foreground">
            The intake never asks for your age, gender, ethnicity, nationality or background, and none of them is used. Skills are self-reported and treated as your own estimate. Roles only appear once the team has verified
            them against a sourced dataset, so the catalogue grows over time instead of guessing.
          </p>
          <p data-enter="item" className="mt-3 text-muted-foreground">
            SDG links come with the reason for each one. They are the team’s mapping, not a United Nations endorsement.
          </p>
        </Card>
      </div>
    </Page>
  )
}
