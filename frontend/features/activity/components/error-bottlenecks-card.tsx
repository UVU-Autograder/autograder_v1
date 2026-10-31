import React from "react";
import { BottleneckItem } from "../types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircleIcon, ShieldAlertIcon, FileCodeIcon, ClockIcon } from "lucide-react";

interface ErrorBottlenecksCardProps {
  bottlenecks: BottleneckItem[];
}

function CategoryIcon({ category }: { category: string }) {
  switch (category) {
    case "syntax_error":
    case "syntax":
      return <FileCodeIcon className="h-4 w-4 text-warning" />;
    case "concept_blocked":
    case "concept":
      return <ShieldAlertIcon className="h-4 w-4 text-destructive" />;
    case "timeout":
      return <ClockIcon className="h-4 w-4 text-warning" />;
    default:
      return <AlertCircleIcon className="h-4 w-4 text-destructive" />;
  }
}

function CategoryBadge({ category }: { category: string }) {
  switch (category) {
    case "syntax_error":
    case "syntax":
      return <Badge variant="outline" className="text-warning border-warning/30">Syntax</Badge>;
    case "concept_blocked":
    case "concept":
      return <Badge variant="outline" className="text-destructive border-destructive/30">AST / Policy</Badge>;
    case "timeout":
      return <Badge variant="outline" className="text-warning border-warning/30">Timeout</Badge>;
    default:
      return <Badge variant="outline" className="text-muted-foreground">Assertion</Badge>;
  }
}

export function ErrorBottlenecksCard({ bottlenecks }: ErrorBottlenecksCardProps) {
  if (bottlenecks.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Failure Bottlenecks</CardTitle>
          <CardDescription>Most frequent assertion failures and syntax/policy errors</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No recurring error bottlenecks detected in this window.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Failure Bottlenecks</CardTitle>
        <CardDescription>Most frequent assertion failures and syntax/policy errors</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-border">
          {bottlenecks.map((item) => (
            <div key={`${item.category}-${item.key}`} className="flex items-start justify-between py-2.5 first:pt-0 last:pb-0">
              <div className="flex items-start gap-2.5 min-w-0 pr-4">
                <div className="mt-0.5 shrink-0">
                  <CategoryIcon category={item.category} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-foreground truncate">
                      {item.key}
                    </span>
                    <CategoryBadge category={item.category} />
                  </div>
                  {item.description ? (
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{item.description}</p>
                  ) : null}
                </div>
              </div>
              <div className="shrink-0 text-right">
                <span className="text-sm font-semibold tabular-nums text-foreground">
                  {item.count}
                </span>
                <span className="text-xs text-muted-foreground ml-1">fails</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
