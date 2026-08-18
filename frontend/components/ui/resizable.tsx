"use client"

import * as ResizablePrimitive from "react-resizable-panels"
import { cn } from "@/lib/utils"
import { ArrowLeftRight } from "lucide-react"

function ResizablePanelGroup({
  className,
  ...props
}: ResizablePrimitive.GroupProps) {
  return (
    <ResizablePrimitive.Group
      data-slot="resizable-panel-group"
      className={cn("flex h-full w-full min-h-0 min-w-0 overflow-hidden", className)}
      {...props}
    />
  )
}

function ResizablePanel({ className, ...props }: ResizablePrimitive.PanelProps) {
  return (
    <ResizablePrimitive.Panel
      data-slot="resizable-panel"
      className={cn("h-full min-w-0 min-h-0 flex flex-col overflow-hidden", className)}
      {...props}
    />
  )
}

function ResizableHandle({
  withHandle,
  className,
  ...props
}: ResizablePrimitive.SeparatorProps & {
  withHandle?: boolean
}) {
  return (
    <ResizablePrimitive.Separator
      data-slot="resizable-handle"
      className={cn(
        "relative flex w-1.5 shrink-0 items-center justify-center bg-border hover:bg-primary/70 active:bg-primary transition-colors cursor-col-resize [&[aria-orientation=horizontal]]:h-1.5 [&[aria-orientation=horizontal]]:w-full [&[aria-orientation=horizontal]]:cursor-row-resize z-10",
        className
      )}
      {...props}
    >
      {withHandle && (
        <div className="pointer-events-none absolute left-1/2 top-1/2 z-20 flex h-4 w-4 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-xs">
          <ArrowLeftRight className="h-2.5 w-2.5" />
        </div>
      )}
    </ResizablePrimitive.Separator>
  )
}

export { ResizableHandle, ResizablePanel, ResizablePanelGroup }
