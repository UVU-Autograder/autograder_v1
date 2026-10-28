import { cn } from "@/lib/utils";

type PageStatusProps = {
  children: React.ReactNode;
  className?: string;
};

export function PageLoading({ children, className }: PageStatusProps) {
  return (
    <div
      role="status"
      className={cn(
        "flex min-h-32 items-center justify-center px-4 py-8 text-sm font-medium text-muted-foreground",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PageEmpty({ children, className }: PageStatusProps) {
  return (
    <div
      role="status"
      className={cn(
        "py-12 text-center text-muted-foreground",
        className,
      )}
    >
      {children}
    </div>
  );
}
