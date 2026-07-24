"use client"

import type { ReactNode } from "react"
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { FileTextIcon, FileCodeIcon, Trash2Icon, FolderIcon } from "lucide-react"

export type NavMainProps = {
  onOpenDetails?: () => void
  workspaceFiles?: string[]
  onOpenFile?: (filename: string) => void
  onDeleteFile?: (filename: string) => void
  fileUploadAction?: ReactNode
  items?: Array<{
    title: string
    url?: string
    icon?: ReactNode
    isActive?: boolean
    items?: Array<{
      title: string
      url?: string
      onClick?: () => void
      onDelete?: () => void
    }>
    actions?: ReactNode
  }>
}

export function NavMain({
  onOpenDetails,
  workspaceFiles,
  onOpenFile,
  onDeleteFile,
  fileUploadAction,
  items,
}: NavMainProps) {
  // If dedicated sandbox workspace props are supplied
  if (onOpenDetails || workspaceFiles) {
    return (
      <SidebarGroup className="space-y-4 px-2 py-2">
        {/* Details button where "Platform" was */}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={onOpenDetails}
              className="w-full font-medium hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer border border-stone-200/80 shadow-xs rounded-md"
              tooltip="Details"
            >
              <FileTextIcon className="size-4 text-indigo-600" />
              <span className="font-semibold text-stone-900 dark:text-stone-100">Details</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {/* Direct Files list below without collapsible dropdowns */}
        <div className="space-y-2 pt-1">
          <div className="px-1 text-[11px] font-bold text-stone-500 uppercase tracking-wider flex items-center gap-1.5">
            <FolderIcon className="size-3.5" />
            <span>Files</span>
          </div>
          <SidebarMenu className="space-y-0.5">
            {workspaceFiles && workspaceFiles.length > 0 ? (
              workspaceFiles.map((filename) => (
                <SidebarMenuItem key={filename} className="group/file flex items-center justify-between">
                  <SidebarMenuButton
                    onClick={() => onOpenFile?.(filename)}
                    className="w-full text-xs font-mono truncate hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer"
                  >
                    <FileCodeIcon className="size-3.5 text-stone-500" />
                    <span className="truncate">{filename}</span>
                  </SidebarMenuButton>
                  {onDeleteFile && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteFile(filename)
                      }}
                      className="mr-1 opacity-0 group-hover/file:opacity-100 text-red-500 hover:text-red-700 transition-opacity p-1 rounded cursor-pointer"
                      title={`Delete ${filename}`}
                    >
                      <Trash2Icon className="size-3.5" />
                    </button>
                  )}
                </SidebarMenuItem>
              ))
            ) : (
              <p className="px-1 py-1 text-xs text-stone-400 italic">No files uploaded yet.</p>
            )}
          </SidebarMenu>
          {fileUploadAction && <div className="pt-2">{fileUploadAction}</div>}
        </div>
      </SidebarGroup>
    )
  }

  // Fallback for generic items list
  return (
    <SidebarGroup className="px-2 py-2">
      <SidebarMenu>
        {items?.map((item) => (
          <SidebarMenuItem key={item.title}>
            <SidebarMenuButton
              onClick={() => {
                if (item.items?.[0]?.onClick) {
                  item.items[0].onClick()
                }
              }}
              tooltip={item.title}
            >
              {item.icon}
              <span>{item.title}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}

