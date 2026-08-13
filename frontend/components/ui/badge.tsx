import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 select-none",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-indigo-600 text-white shadow-xs hover:bg-indigo-700",
        secondary:
          "border-transparent bg-slate-100 text-slate-800 hover:bg-slate-200",
        success:
          "border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
        destructive:
          "border-transparent bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300",
        warning:
          "border-transparent bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-300",
        outline:
          "border border-slate-200 text-slate-700 dark:border-slate-800 dark:text-slate-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
