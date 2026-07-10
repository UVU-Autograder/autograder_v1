import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type BackLinkProps = {
  href: string;
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "compact" | "sidebar";
};

const variantClasses = {
  default: "mb-4 -ml-2",
  compact: "-ml-3",
  sidebar: "w-full justify-start",
} as const;

export function BackLink({
  href,
  children,
  className,
  variant = "default",
}: BackLinkProps) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn(variantClasses[variant], className)}
      asChild
    >
      <Link href={href}>
        <ArrowLeftIcon />
        {children}
      </Link>
    </Button>
  );
}
