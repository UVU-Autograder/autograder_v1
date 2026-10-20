"use client";

import { useEffect, useState } from "react";
import { BackLink } from "@/components/back-link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  getAdminLogs,
  getAdminLogStats,
  verifyAdminLogs,
} from "@/features/audit/api";
import {
  AuditRecord,
  AuditStatsResponse,
  AuditVerificationResponse,
} from "@/features/audit/types";

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState<AuditStatsResponse | null>(null);

  const [search, setSearch] = useState("");
  const [selectedEvent, setSelectedEvent] = useState("");
  const [selectedWorkflow, setSelectedWorkflow] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [verificationResult, setVerificationResult] =
    useState<AuditVerificationResponse | null>(null);
  const [inspectingRecord, setInspectingRecord] = useState<AuditRecord | null>(null);

  const fetchStats = async () => {
    try {
      const data = await getAdminLogStats();
      setStats(data);
    } catch (err) {
      console.error("Failed to load stats:", err);
    }
  };

  const fetchLogs = async (targetPage = page) => {
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await getAdminLogs({
        page: targetPage,
        page_size: 25,
        search: search.trim() || undefined,
        event: selectedEvent || undefined,
        workflow_type: selectedWorkflow || undefined,
      });
      setLogs(data.items);
      setTotal(data.total);
      setPage(data.page);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
      setError(err instanceof Error ? err.message : "Failed to load audit logs.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    getAdminLogStats()
      .then((data) => {
        if (!ignore) setStats(data);
      })
      .catch((err) => {
        console.error("Failed to load stats:", err);
      });
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;
    getAdminLogs({
      page: 1,
      page_size: 25,
      search: search.trim() || undefined,
      event: selectedEvent || undefined,
      workflow_type: selectedWorkflow || undefined,
    })
      .then((data) => {
        if (!ignore) {
          setLogs(data.items);
          setTotal(data.total);
          setPage(data.page);
          setTotalPages(data.total_pages);
        }
      })
      .catch((err) => {
        if (!ignore) {
          console.error("Failed to load audit logs:", err);
          setError(err instanceof Error ? err.message : "Failed to load audit logs.");
        }
      })
      .finally(() => {
        if (!ignore) {
          setIsLoading(false);
          setIsRefreshing(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [search, selectedEvent, selectedWorkflow]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void fetchLogs(1);
  };

  const handleResetFilters = () => {
    setSearch("");
    setSelectedEvent("");
    setSelectedWorkflow("");
  };

  const handleRunVerification = async () => {
    setIsVerifying(true);
    setError(null);
    try {
      const res = await verifyAdminLogs(500);
      setVerificationResult(res);
    } catch (err) {
      console.error("Verification failed:", err);
      setError(err instanceof Error ? err.message : "FERPA verification scan failed.");
    } finally {
      setIsVerifying(false);
    }
  };

  const getEventBadge = (event: string) => {
    if (event.startsWith("auth.access_denied")) {
      return <Badge variant="destructive">{event}</Badge>;
    }
    if (event.startsWith("audit.pii_redacted")) {
      return <Badge variant="warning">{event}</Badge>;
    }
    if (event.includes("failed")) {
      return <Badge variant="destructive">{event}</Badge>;
    }
    if (event.includes("completed") || event.includes("success")) {
      return <Badge variant="success">{event}</Badge>;
    }
    return <Badge variant="secondary">{event}</Badge>;
  };

  if (isLoading && !logs.length) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="font-medium text-muted-foreground">Loading audit records...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pt-8 pb-16">
      <BackLink href="/staff/admin">Back to admin</BackLink>

      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Audit Logs</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunVerification}
            disabled={isVerifying}
          >
            {isVerifying ? "Scanning..." : "Verify FERPA"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              void fetchStats();
              void fetchLogs(page);
            }}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </div>

      {/* Compact Status Strip */}
      <div className="mb-4 flex flex-wrap items-center gap-6 rounded-md border border-border bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        <div>Total: <span className="font-mono font-medium text-foreground">{stats?.total_events ?? 0}</span></div>
        <div>Last 24h: <span className="font-mono font-medium text-foreground">{stats?.events_24h ?? 0}</span></div>
        <div>Redacted PII: <span className="font-mono font-medium text-foreground">{stats?.pii_redacted_count ?? 0}</span></div>
        <div>Access Denials: <span className="font-mono font-medium text-foreground">{stats?.access_denied_count ?? 0}</span></div>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Verification Result */}
      {verificationResult && (
        <div
          className={`mb-4 flex items-start justify-between rounded-md border p-3 text-xs ${
            verificationResult.compliant
              ? "border-success/30 bg-success/10 text-success"
              : "border-destructive/30 bg-destructive/10 text-destructive"
          }`}
        >
          <div>
            <span className="font-semibold">
              {verificationResult.compliant
                ? `FERPA Compliant: 0 residual PII patterns detected across ${verificationResult.records_scanned} records.`
                : `Compliance Alert: ${verificationResult.violations_count} potential unredacted pattern match(es) detected.`}
            </span>
            <span className="ml-2 text-muted-foreground">{verificationResult.disclaimer}</span>
            {verificationResult.violations.length > 0 && (
              <ul className="mt-2 list-disc pl-4 space-y-0.5">
                {verificationResult.violations.map((v, i) => (
                  <li key={i}>
                    Record #{v.record_id} ({v.event}) in field <code>{v.field}</code> matched {v.matched_rule}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <button
            onClick={() => setVerificationResult(null)}
            className="ml-4 shrink-0 text-muted-foreground hover:text-foreground text-sm font-semibold"
            aria-label="Dismiss"
          >
            &times;
          </button>
        </div>
      )}

      {/* Toolbar: Search & Filters */}
      <form onSubmit={handleSearchSubmit} className="mb-4 flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search event, course, or workflow..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-9 max-w-xs text-xs"
        />
        <select
          value={selectedEvent}
          onChange={(e) => setSelectedEvent(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">All Events</option>
          <option value="auth.access_denied">auth.access_denied</option>
          <option value="official.run_completed">official.run_completed</option>
          <option value="sandbox.run_completed">sandbox.run_completed</option>
          <option value="audit.pii_redacted">audit.pii_redacted</option>
          <option value="official.cleanup_failed">official.cleanup_failed</option>
          <option value="judge0.cleanup_failed">judge0.cleanup_failed</option>
          <option value="official.workspace_deleted">official.workspace_deleted</option>
        </select>
        <select
          value={selectedWorkflow}
          onChange={(e) => setSelectedWorkflow(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">All Workflows</option>
          <option value="official">official</option>
          <option value="sandbox">sandbox</option>
          <option value="logging">logging</option>
        </select>
        <Button type="submit" size="sm" variant="secondary">
          Search
        </Button>
        {(search || selectedEvent || selectedWorkflow) && (
          <Button type="button" variant="ghost" size="sm" onClick={handleResetFilters}>
            Reset
          </Button>
        )}
      </form>

      {/* Main Records Table Card */}
      <Card>
        <CardHeader className="py-3 px-4 border-b">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {total} {total === 1 ? "Record" : "Records"}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 text-xs font-medium text-muted-foreground">
                <tr className="border-b">
                  <th className="px-4 py-2.5">Timestamp (UTC)</th>
                  <th className="px-4 py-2.5">Event</th>
                  <th className="px-4 py-2.5">Workflow</th>
                  <th className="px-4 py-2.5">Subject</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-xs text-muted-foreground">
                      No audit records found.
                    </td>
                  </tr>
                ) : (
                  logs.map((record) => (
                    <tr key={record.id} className="hover:bg-muted/20 transition-colors text-xs">
                      <td className="px-4 py-2.5 font-mono text-muted-foreground whitespace-nowrap">
                        {new Date(record.timestamp).toISOString()}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        {getEventBadge(record.event)}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap text-muted-foreground">
                        {record.workflow_type || "—"}
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">
                        {record.actor_user_id ? `Staff #${record.actor_user_id}` : ""}
                        {record.course_id ? ` · ${record.course_id}` : ""}
                        {record.run_id ? ` · Run #${record.run_id}` : ""}
                        {!record.actor_user_id && !record.course_id && !record.run_id && "System"}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap font-mono">
                        {record.status_code || "—"}
                      </td>
                      <td className="px-4 py-2.5 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          onClick={() => setInspectingRecord(record)}
                        >
                          Payload
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t px-4 py-2 text-xs text-muted-foreground">
            <div>
              Showing {logs.length} of {total} records
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => fetchLogs(page - 1)}
                disabled={page <= 1 || isRefreshing}
              >
                Previous
              </Button>
              <span className="px-2">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => fetchLogs(page + 1)}
                disabled={page >= totalPages || isRefreshing}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Payload Modal */}
      <Dialog
        open={inspectingRecord !== null}
        onOpenChange={(open) => {
          if (!open) setInspectingRecord(null);
        }}
      >
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <span>Record #{inspectingRecord?.id}</span>
              {inspectingRecord && getEventBadge(inspectingRecord.event)}
            </DialogTitle>
          </DialogHeader>
          {inspectingRecord && (
            <pre className="mt-2 max-h-96 overflow-auto rounded-md bg-muted p-3 font-mono text-xs text-foreground">
              {JSON.stringify(inspectingRecord.payload, null, 2)}
            </pre>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
