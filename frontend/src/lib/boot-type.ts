import type { BootSegment } from '@/content/landing'

const SEGMENT_CLASS: Record<NonNullable<BootSegment['kind']>, string> = {
  prompt: 'boot-prompt',
  demo: 'boot-demo',
  ok: 'boot-ok',
  dim: 'boot-dim',
}

function render(line: BootSegment[], upTo: number, cursor: boolean) {
  const frag = document.createDocumentFragment()
  let left = upTo
  for (const seg of line) {
    if (left <= 0) break
    const span = document.createElement('span')
    if (seg.kind) span.className = SEGMENT_CLASS[seg.kind]
    span.textContent = seg.text.slice(0, left)
    left -= seg.text.length
    frag.append(span)
  }
  if (cursor) {
    const c = document.createElement('span')
    c.className = 'boot-cursor'
    c.textContent = '▊'
    frag.append(c)
  }
  return frag
}

/**
 * Types boot lines into `host`, two characters every 14 ms with a 180 ms pause between
 * lines (the 0xmyth cadence). Writes the DOM directly so React doesn't re-render per
 * character. Returns a promise for the end, `finish()` to print everything now, and
 * `cancel()` to stop without resolving (effect clean-up).
 */
export function typeLines(host: HTMLElement, lines: BootSegment[][], { step = 14, gap = 180, perStep = 2 } = {}) {
  host.replaceChildren()
  const rows = lines.map(() => host.appendChild(document.createElement('div')))
  const lengths = lines.map((l) => l.reduce((n, s) => n + s.text.length, 0))
  let timer = 0
  let done: () => void = () => {}
  const finished = new Promise<void>((resolve) => {
    done = resolve
  })

  const cancel = () => clearTimeout(timer)
  const finish = () => {
    clearTimeout(timer)
    rows.forEach((row, i) => row.replaceChildren(render(lines[i], lengths[i], false)))
    done()
  }

  let li = 0
  let ci = 0
  const tick = () => {
    ci = Math.min(lengths[li], ci + perStep)
    rows[li].replaceChildren(render(lines[li], ci, true))
    if (ci < lengths[li]) {
      timer = window.setTimeout(tick, step)
      return
    }
    rows[li].replaceChildren(render(lines[li], ci, false))
    li++
    ci = 0
    if (li < lines.length) timer = window.setTimeout(tick, gap)
    else done()
  }
  if (lines.length) tick()
  else done()

  return { finished, finish, cancel }
}
