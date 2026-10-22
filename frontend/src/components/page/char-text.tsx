/**
 * Renders text as masked words of single characters so they can rise in one by one.
 * Screen readers get the plain string; the split copy is hidden from them.
 */
export function CharText({ text }: { text: string }) {
  return (
    <>
      <span className="sr-only">{text}</span>
      <span aria-hidden>
        {text.split(' ').map((word, w) => (
          <span key={w}>
            {w > 0 && ' '}
            <span className="split-word">
              {Array.from(word).map((ch, i) => (
                <span key={i} className="split-ch">
                  {ch}
                </span>
              ))}
            </span>
          </span>
        ))}
      </span>
    </>
  )
}
