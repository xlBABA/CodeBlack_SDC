import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { field, labelCls } from './form'

export function ProjectsEditor({ projects, onChange }: { projects: string[]; onChange: (projects: string[]) => void }) {
  const [text, setText] = useState('')
  const add = () => {
    if (!text.trim()) return
    onChange([...projects, text.trim()])
    setText('')
  }
  return (
    <div>
      <label htmlFor="project" className={labelCls}>
        Projects you have done
      </label>
      <div className="flex gap-2">
        <input
          id="project"
          className={field}
          placeholder="e.g. Sales dashboard in Excel for a club"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              add()
            }
          }}
        />
        <Button type="button" variant="secondary" onClick={add} disabled={!text.trim()}>
          <Plus />
          Add
        </Button>
      </div>
      {projects.length > 0 && (
        <ul className="mt-3 grid gap-2">
          {projects.map((p, i) => (
            <li key={`${p}-${i}`} data-enter="item" className="flex items-center gap-3 rounded-tile bg-well p-2 pl-4">
              <span className="flex-1">{p}</span>
              <button type="button" aria-label={`Remove ${p}`} onClick={() => onChange(projects.filter((_, k) => k !== i))} className="grid size-8 place-items-center rounded-full text-muted-foreground hover:bg-raised">
                <X className="size-4" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
