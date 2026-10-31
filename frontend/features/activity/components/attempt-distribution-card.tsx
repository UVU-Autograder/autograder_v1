import React from "react";
import { AttemptBucket } from "../types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface AttemptDistributionCardProps {
  distribution: AttemptBucket[];
}

export function AttemptDistributionCard({ distribution }: AttemptDistributionCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Attempt Distribution</CardTitle>
        <CardDescription>Number of sandbox submissions per student before completion or stopping</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {distribution.map((bucket) => (
            <div key={bucket.bucket_label} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-foreground">{bucket.bucket_label}</span>
                <span className="tabular-nums text-muted-foreground">
                  {bucket.session_count} students ({bucket.percentage}%)
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary/75 transition-all"
                  style={{ width: `${Math.max(bucket.percentage, bucket.session_count > 0 ? 3 : 0)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
