"use client";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function Navbar() {
  const [role, setRole] = useState<"admin" | "student">("student");
  const switchRole = () => {
    const newRole = role === "student" ? "admin" : "student";
    setRole(newRole);
    localStorage.setItem("role", newRole);
  };
    return (
      <div className="sticky top-0 z-50 flex h-15 w-full items-center justify-between border-b border-gray-300 bg-background px-6">
        <NavigationMenu>
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuLink href={`/courses`}>
                Dashboard
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem className={role == "student" ? "hidden" : ""}>
              <NavigationMenuLink href={`/admin`}>
                Admin
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem className={role == "student" ? "" : "hidden"}>
              <NavigationMenuLink href={`/courses/cs1400/assignments/`}>
                Sandbox
              </NavigationMenuLink>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
        <Button onClick={switchRole} className="shrink-0">
          {role == "student" ? "Switch to Admin View" : "Switch to Student View"}
        </Button>
      </div>
    )
}