"use client";

import { useEffect, useState } from "react";
import { RefreshCwIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { getAdminMonitoring, MonitoringStats } from "@/features/courses/api";

function formatTime(value: string | null | undefined): string {
  if (!value) return "Never reported";
  return new Date(value).toLocaleString();
}

function MetricRow({
  label,
  value,
  note,
}: {
  label: string;
  value: React.ReactNode;
  note?: string;
}) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-4 py-2.5 border-b border-border last:border-b-0">
      <div className="min-w-0">
        <div className="text-sm text-foreground">{label}</div>
        {note ? <p className="text-xs text-muted-foreground mt-0.5">{note}</p> : null}
      </div>
      <div className="text-sm font-medium tabular-nums text-foreground text-right">
        {value}
      </div>
    </div>
  );
}

function HealthValue({ ok, okLabel, badLabel }: { ok: boolean; okLabel: string; badLabel: string }) {
  return (
    <span className={ok ? "text-success" : "text-destructive"}>
      {ok ? okLabel : badLabel}
    </span>
  );
}

export default function MonitoringPage() {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStats = async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await getAdminMonitoring();
      setStats(data);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load monitoring stats.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    void Promise.resolve().then(fetchStats);

    const interval = setInterval(() => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        void fetchStats();
      }
    }, 10000);

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void fetchStats();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, []);

  if (isLoading) {
    return <PageLoading className="h-screen">Loading system metrics...</PageLoading>;
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-4 pt-8 pb-12">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: "Admin", href: "/staff/admin" },
          { label: "Monitoring" },
        ]}
      />

      <AdminPageHeader
        title="Monitoring"
        description="Queue depth, cleanup health, and local AI usage."
        actions={
          <Button variant="outline" size="sm" onClick={fetchStats} disabled={isRefreshing}>
            <RefreshCwIcon className={`mr-1 size-4 ${isRefreshing ? "animate-spin" : ""}`} />
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      {error && (
        <div className="mb-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <section className="mb-8">
        <h2 className="mb-1 text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          Health
        </h2>
        <div role="status">
          <MetricRow
            label="Official data cleanup"
            value={
              <HealthValue
                ok={Boolean(stats?.cleanup_service_healthy)}
                okLabel="Healthy"
                badLabel="Unhealthy"
              />
            }
            note={`${stats?.cleanup_failed_runs ?? 0} failed · ${stats?.cleanup_overdue_runs ?? 0} overdue · ${stats?.cleanup_orphan_errors ?? 0} sweep errors · last check ${formatTime(stats?.cleanup_last_checked_at)}`}
          />
          <MetricRow
            label="Execution dispatch"
            value={
              <HealthValue
                ok={Boolean(stats?.dispatch_service_healthy)}
                okLabel="Healthy"
                badLabel="Unhealthy"
              />
            }
            note="Official batches wait separately for execution capacity."
          />
        </div>
      </section>

      <section>
        <h2 className="mb-1 text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          Activity
        </h2>
        <div>
          <MetricRow label="Active executions" value={stats?.active_executions ?? stats?.active_runs_count ?? 0} />
          <MetricRow label="Waiting executions" value={stats?.waiting_executions ?? stats?.queued_runs_count ?? 0} />
          <MetricRow
            label="Sandbox uploads (past hour)"
            value={stats?.sandbox_runs_last_hour ?? 0}
          />
          <MetricRow
            label="Local AI tokens (total)"
            value={(stats?.total_token_usage ?? 0).toLocaleString()}
          />
        </div>
      </section>
    </div>
  );
}
