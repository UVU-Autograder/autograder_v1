"use client"

import * as React from "react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"

type AppSidebarData = {
  header?: React.ReactNode
  onOpenDetails?: () => void
  workspaceFiles?: string[]
  onOpenFile?: (filename: string) => void
  onDeleteFile?: (filename: string) => void
  fileUploadAction?: React.ReactNode
  user?: {
    name: string
    email: string
    avatar: string
  }
  teams?: Array<{
    name: string
    logo: React.ReactNode
    plan: string
  }>
  navMain?: Array<{
    title: string
    url?: string
    icon?: React.ReactNode
    isActive?: boolean
    items?: Array<{
      title: string
      url?: string
      onClick?: () => void
    }>
    actions?: React.ReactNode
  }>
  projects?: Array<{
    name: string
    url: string
    icon: React.ReactNode
  }>
}

export function AppSidebar({ data, ...props }: React.ComponentProps<typeof Sidebar> & { data: AppSidebarData }) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        {data.header}
        {data.teams && <TeamSwitcher teams={data.teams} />}
      </SidebarHeader>
      <SidebarContent>
        <NavMain
          onOpenDetails={data.onOpenDetails}
          workspaceFiles={data.workspaceFiles}
          onOpenFile={data.onOpenFile}
          onDeleteFile={data.onDeleteFile}
          fileUploadAction={data.fileUploadAction}
          items={data.navMain}
        />
        {data.projects && <NavProjects projects={data.projects} />}
      </SidebarContent>
      <SidebarFooter>
        {data.user && <NavUser user={data.user} />}
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
