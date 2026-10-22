import { cva, type VariantProps } from 'class-variance-authority'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { pressPop } from '@/lib/motion'
import { cn } from '@/lib/utils'

const iconButtonVariants = cva(
  "relative inline-grid flex-none place-items-center border text-foreground transition-colors duration-150 outline-none [@media(hover:none)]:active:opacity-70 [&_svg]:size-[19px]",
  {
    variants: {
      variant: {
        glass: 'size-11 rounded-full border-rim bg-glass-2 backdrop-blur-md hover:bg-raised dark:border-line',
        plain: 'size-10 rounded-full border-line-2 hover:bg-well',
        ghost: 'size-10 rounded-full border-transparent hover:bg-well',
      },
    },
    defaultVariants: { variant: 'plain' },
  },
)

type IconButtonProps = Omit<React.ComponentProps<'button'>, 'aria-label'> &
  VariantProps<typeof iconButtonVariants> & {
    /** required: icon-only buttons need an accessible name, also shown as the tooltip */
    label: string
  }

export function IconButton({ label, variant, className, onClick, children, ...props }: IconButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={label}
          className={cn(iconButtonVariants({ variant }), className)}
          onClick={(e) => {
            pressPop(e.currentTarget)
            onClick?.(e)
          }}
          {...props}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
