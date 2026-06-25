"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeftIcon, RefreshCwIcon, CpuIcon, ActivityIcon, HourglassIcon, BarChart2Icon } from "lucide-react";
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
    fetchStats();
    
    // Poll stats every 10 seconds
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="animate-pulse font-medium text-slate-500">Loading system metrics...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
        <Link href="/staff/admin">
          <ArrowLeftIcon className="mr-1 size-4" />
          Back to admin
        </Link>
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">System Monitoring</h1>
          <p className="text-sm text-slate-500 mt-0.5">Real-time status of grading queues and API token consumption</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats} disabled={isRefreshing}>
          <RefreshCwIcon className={`mr-1 size-4 ${isRefreshing ? 'animate-spin' : ''}`} /> 
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Active Runs Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase">Active Executions</CardTitle>
              <CardDescription>Grading tasks currently running</CardDescription>
            </div>
            <ActivityIcon className="size-6 text-green-500" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-slate-900">
              {stats?.active_runs_count ?? 0}
            </span>
            <span className="text-xs text-slate-500 ml-2">runs running now</span>
          </CardContent>
        </Card>

        {/* Queued Runs Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase">Queued Executions</CardTitle>
              <CardDescription>Grading tasks waiting in queue</CardDescription>
            </div>
            <HourglassIcon className="size-6 text-amber-500" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-slate-900">
              {stats?.queued_runs_count ?? 0}
            </span>
            <span className="text-xs text-slate-500 ml-2">runs in waiting queue</span>
          </CardContent>
        </Card>

        {/* Sandbox Upload Rates Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase">Sandbox Upload Velocity</CardTitle>
              <CardDescription>Public sandbox submissions in the last hour</CardDescription>
            </div>
            <CpuIcon className="size-6 text-blue-500" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-slate-900">
              {stats?.sandbox_runs_last_hour ?? 0}
            </span>
            <span className="text-xs text-slate-500 ml-2">uploads in past hour</span>
          </CardContent>
        </Card>

        {/* Azure OpenAI Token Usage Card */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase">Azure OpenAI Tokens</CardTitle>
              <CardDescription>Accumulated token counts for generated AI feedback</CardDescription>
            </div>
            <BarChart2Icon className="size-6 text-purple-500" />
          </CardHeader>
          <CardContent className="pt-2">
            <span className="text-4xl font-extrabold tracking-tight text-slate-900">
              {stats?.total_token_usage?.toLocaleString() ?? 0}
            </span>
            <span className="text-xs text-slate-500 ml-2">tokens total</span>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
