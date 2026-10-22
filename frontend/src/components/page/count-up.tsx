import { COUNT_FORMATS, type CountFormat } from '@/lib/motion'

/**
 * A number that counts up when its page enters. The value always comes from data (mocks/API);
 * this component only formats and animates it. The visible digits are hidden from assistive
 * tech, which reads the final value instead of every intermediate frame.
 */
export function CountUp({ value, format = 'int', className }: { value: number; format?: CountFormat; className?: string }) {
  const text = COUNT_FORMATS[format](value)
  return (
    <span className={className}>
      <span data-count={value} data-format={format} aria-hidden className="tabular-nums">
        {text}
      </span>
      <span className="sr-only">{text}</span>
    </span>
  )
}
