import React from "react";
import { SearchIcon } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { StatusFilter } from "../types";

interface StudentFilterToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  statusFilter: StatusFilter;
  onStatusFilterChange: (filter: StatusFilter) => void;
  counts: {
    all: number;
    ungraded: number;
    graded: number;
    failed: number;
  };
}

export function StudentFilterToolbar({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  counts,
}: StudentFilterToolbarProps) {
  return (
    <div className="space-y-3">
      <div className="relative">
        <SearchIcon className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search by student name or Canvas ID..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9 text-sm"
          data-testid="student-search-input"
        />
      </div>

      <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Filter students by grading status">
        <Button
          type="button"
          variant={statusFilter === "all" ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs px-2.5"
          onClick={() => onStatusFilterChange("all")}
          data-testid="filter-all"
        >
          All ({counts.all})
        </Button>
        <Button
          type="button"
          variant={statusFilter === "ungraded" ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs px-2.5"
          onClick={() => onStatusFilterChange("ungraded")}
          data-testid="filter-ungraded"
        >
          Needs Grading ({counts.ungraded})
        </Button>
        <Button
          type="button"
          variant={statusFilter === "graded" ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs px-2.5"
          onClick={() => onStatusFilterChange("graded")}
          data-testid="filter-graded"
        >
          Graded ({counts.graded})
        </Button>
        <Button
          type="button"
          variant={statusFilter === "failed" ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs px-2.5"
          onClick={() => onStatusFilterChange("failed")}
          data-testid="filter-failed"
        >
          Failed ({counts.failed})
        </Button>
      </div>
    </div>
  );
}
