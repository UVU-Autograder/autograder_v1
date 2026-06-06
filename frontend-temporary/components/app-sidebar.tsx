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
  navMain: Array<{
    title: string
    url: string
    icon: React.ReactNode
    isActive?: boolean
    items?: Array<{
      title: string
      url?: string
      onClick?: () => void
    }>
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
        {data.teams && <TeamSwitcher teams={data.teams} />}
      </SidebarHeader>
      <SidebarContent>
        {data.navMain && <NavMain items={data.navMain} />}
        {data.projects && <NavProjects projects={data.projects} />}
      </SidebarContent>
      <SidebarFooter>
        {data.user && <NavUser user={data.user} />}
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
