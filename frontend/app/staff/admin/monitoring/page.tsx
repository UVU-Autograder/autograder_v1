"use client";

import { useEffect, useState } from "react";
import { RefreshCwIcon, CpuIcon, ActivityIcon, HourglassIcon, BarChart2Icon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getAdminMonitoring, MonitoringStats } from "@/features/courses/api";

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
    
    // Poll stats every 10 seconds
    const interval = setInterval(() => void fetchStats(), 10000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="animate-pulse font-medium text-muted-foreground">Loading system metrics...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <BackLink href="/staff/admin">Back to admin</BackLink>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">System Monitoring</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Real-time status of grading queues and API token consumption</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats} disabled={isRefreshing}>
          <RefreshCwIcon className={`mr-1 size-4 ${isRefreshing ? 'animate-spin' : ''}`} /> 
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive font-medium">
          {error}
        </div>
      )}

      <Card className="mb-4">
        <CardHeader><CardTitle>Official data cleanup</CardTitle></CardHeader>
        <CardContent>
          <p role="status">{stats?.cleanup_service_healthy ? "Cleanup service healthy" : "Cleanup service unhealthy or heartbeat missing"}</p>
          <p>{stats?.cleanup_failed_runs ?? 0} failed cleanups · {stats?.cleanup_overdue_runs ?? 0} runs past the 24-hour deletion deadline · {stats?.cleanup_orphan_errors ?? 0} sweep errors</p>
          <p className="text-sm text-muted-foreground">Last check: {stats?.cleanup_last_checked_at ? new Date(stats.cleanup_last_checked_at).toLocaleString() : "Never reported"}</p>
        </CardContent>
      </Card>
      <Card className="mb-4">
        <CardHeader><CardTitle>Execution dispatch</CardTitle></CardHeader>
        <CardContent>
          <p role="status">{stats?.dispatch_service_healthy ? "Dispatcher healthy" : "Dispatcher unhealthy or heartbeat missing"}</p>
          <p>{stats?.active_executions ?? 0} active executions · {stats?.waiting_executions ?? 0} waiting executions</p>
          <p className="text-sm text-muted-foreground">Official batches wait separately for execution capacity.</p>
        </CardContent>
      </Card>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Active Runs Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Active Executions</CardTitle>
              <CardDescription>Grading tasks currently running</CardDescription>
            </div>
            <ActivityIcon className="size-6 text-success" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-foreground">
              {stats?.active_runs_count ?? 0}
            </span>
            <span className="text-xs text-muted-foreground ml-2">runs running now</span>
          </CardContent>
        </Card>

        {/* Queued Runs Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Queued Executions</CardTitle>
              <CardDescription>Grading tasks waiting in queue</CardDescription>
            </div>
            <HourglassIcon className="size-6 text-warning" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-foreground">
              {stats?.queued_runs_count ?? 0}
            </span>
            <span className="text-xs text-muted-foreground ml-2">runs in waiting queue</span>
          </CardContent>
        </Card>

        {/* Sandbox Upload Rates Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Sandbox Upload Velocity</CardTitle>
              <CardDescription>Public sandbox submissions in the last hour</CardDescription>
            </div>
            <CpuIcon className="size-6 text-primary" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-foreground">
              {stats?.sandbox_runs_last_hour ?? 0}
            </span>
            <span className="text-xs text-muted-foreground ml-2">uploads in past hour</span>
          </CardContent>
        </Card>

        {/* Local LLM Token Usage Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Local LLM Tokens</CardTitle>
              <CardDescription>Accumulated token counts for generated local AI feedback</CardDescription>
            </div>
            <BarChart2Icon className="size-6 text-primary" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-foreground">
              {stats?.total_token_usage?.toLocaleString() ?? 0}
            </span>
            <span className="text-xs text-muted-foreground ml-2">tokens total</span>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
