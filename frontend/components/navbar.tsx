"use client";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
import { Button } from "@/components/ui/button";
import { usePathname, useRouter } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const isStaffOrAdmin = pathname.startsWith("/staff") || pathname.startsWith("/admin");

  const switchRole = () => {
    if (isStaffOrAdmin) {
      router.push("/sandbox/courses");
    } else {
      router.push("/staff/courses");
    }
  };

  return (
    <div className="sticky top-0 z-50 flex h-15 w-full items-center justify-between border-b border-gray-300 bg-background px-6">
      <NavigationMenu>
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink href={isStaffOrAdmin ? "/staff/courses" : "/sandbox/courses"}>
              Dashboard
            </NavigationMenuLink>
          </NavigationMenuItem>
          {isStaffOrAdmin && (
            <NavigationMenuItem>
              <NavigationMenuLink href="/admin">
                Admin
              </NavigationMenuLink>
            </NavigationMenuItem>
          )}
          {!isStaffOrAdmin && (
            <NavigationMenuItem>
              <NavigationMenuLink href="/sandbox/courses/cs1400/assignments/">
                Sandbox
              </NavigationMenuLink>
            </NavigationMenuItem>
          )}
        </NavigationMenuList>
      </NavigationMenu>
      <Button onClick={switchRole} className="shrink-0">
        {isStaffOrAdmin ? "Switch to Student View" : "Switch to Staff View"}
      </Button>
    </div>
  );
}