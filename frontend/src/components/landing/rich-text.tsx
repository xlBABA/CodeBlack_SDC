import { Fragment } from 'react'
import { richWords } from '@/lib/rich-words'

export function RichLine({ text }: { text: string }) {
  return (
    <>
      {richWords(text).map((w, i) => (
        <Fragment key={i}>
          {i > 0 && ' '}
          {w.accent ? <span className="serif text-primary">{w.word}</span> : w.word}
        </Fragment>
      ))}
    </>
  )
}
