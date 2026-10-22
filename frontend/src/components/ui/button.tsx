import { useRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { Slot } from 'radix-ui'
import { useMagnetic } from '@/hooks/use-hover-fx'
import { cn, mergeRefs } from '@/lib/utils'

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 rounded-ctl border border-transparent font-[650] whitespace-nowrap transition-[background-color,border-color,color,box-shadow] duration-150 outline-none select-none disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [@media(hover:none)]:active:opacity-70 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-[17px]",
  {
    variants: {
      variant: {
        primary:
          'bg-primary text-primary-foreground shadow-[0_12px_24px_-14px_color-mix(in_srgb,var(--primary)_90%,transparent)] hover:bg-[color-mix(in_srgb,var(--primary)_88%,var(--text))]',
        secondary: 'border-rim bg-glass-2 text-foreground shadow-card backdrop-blur-md hover:bg-raised dark:border-line',
        ink: 'bg-ink text-ink-foreground hover:bg-[color-mix(in_srgb,var(--ink)_86%,var(--bg))]',
        ghost: 'text-foreground hover:bg-well',
        link: 'h-auto px-0 text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-11 px-5 text-base',
        sm: 'h-9 gap-1.5 px-3.5 text-sm',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: { variant: 'primary', size: 'default' },
  },
)

type ButtonProps = React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
    /** drift toward the pointer (desktop only) */
    magnetic?: boolean
  }

function Button({ className, variant, size, asChild = false, magnetic = false, ref, ...props }: ButtonProps) {
  const own = useRef<HTMLButtonElement>(null)
  useMagnetic(own, magnetic)
  const Comp = asChild ? Slot.Root : 'button'
  return (
    <Comp
      ref={mergeRefs(own, ref)}
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

// oxlint-disable-next-line react/only-export-components
export { Button, buttonVariants }
