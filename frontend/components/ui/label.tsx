import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const labelVariants = cva(
  "text-sm font-semibold leading-none text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-70 select-none"
)

function Label({ className, ...props }: React.ComponentProps<"label"> & VariantProps<typeof labelVariants>) {
  return (
    <label
      className={cn(labelVariants(), className)}
      {...props}
    />
  )
}

export { Label }
