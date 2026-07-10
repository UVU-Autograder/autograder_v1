"use client"

import type { ReactNode } from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import { ChevronRightIcon, Trash2Icon } from "lucide-react"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: React.ReactNode
    isActive?: boolean
    items?: {
      title: string
      url?: string
      onClick?: () => void
      onDelete?: () => void
    }[]
    actions?: ReactNode
  }[]
}) {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <Collapsible
            key={item.title}
            asChild
            defaultOpen={item.isActive}
            className="group/collapsible"
          >
            <SidebarMenuItem>
              <CollapsibleTrigger asChild>
                <SidebarMenuButton tooltip={item.title}>
                  {item.icon}
                  <span>{item.title}</span>
                  <ChevronRightIcon className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                </SidebarMenuButton>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarMenuSub>
                  {item.items?.map((subItem) => (
                    <SidebarMenuSubItem key={subItem.title} className="flex items-center justify-between group/sub">
                      <SidebarMenuSubButton asChild>
                        {subItem.url ? (
                          <a href={subItem.url}>
                            <span>{subItem.title}</span>
                          </a>
                        ) : subItem.onClick ? (
                          <button
                            type="button"
                            onClick={subItem.onClick}
                            className="w-full cursor-pointer text-left truncate"
                          >
                            <span>{subItem.title}</span>
                          </button>
                     
                        ) : (
                          <span>{subItem.title}</span>
                        )}
                      </SidebarMenuSubButton>
                      {subItem.onDelete && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            subItem.onDelete!();
                          }}
                          className="mr-2 opacity-0 group-hover/sub:opacity-100 text-red-500 hover:text-red-700 transition-opacity p-0.5 rounded cursor-pointer"
                          aria-label={`Delete ${subItem.title}`}
                        >
                          <Trash2Icon className="size-3" />
                        </button>
                      )}
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
                {item.actions ? (
                  <div className="px-2 py-1">{item.actions}</div>
                ) : null}
              </CollapsibleContent>
            </SidebarMenuItem>
          </Collapsible>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}
