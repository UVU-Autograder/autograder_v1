import { useState, useMemo } from 'react';
import {
  filterStudents,
  hasUngradedManualItems,
} from '@/features/runs/lib/student-filter';
import type { StatusFilter, StudentRunDetail } from '@/features/runs/types';

export interface FilterCounts {
  all: number;
  ungraded: number;
  graded: number;
  failed: number;
}

export function useStudentRunFilters(students: StudentRunDetail[] | undefined) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const filterCounts = useMemo<FilterCounts>(() => {
    const counts = { all: 0, ungraded: 0, graded: 0, failed: 0 };
    for (const s of students ?? []) {
      counts.all += 1;
      const isUngraded =
        Object.keys(s.manual_results ?? {}).length > 0 &&
        hasUngradedManualItems(s);
      if (isUngraded) {
        counts.ungraded += 1;
      } else {
        counts.graded += 1;
      }
      if (s.status === 'failure') {
        counts.failed += 1;
      }
    }
    return counts;
  }, [students]);

  const filteredStudents = useMemo(
    () => filterStudents(students ?? [], searchQuery, statusFilter),
    [students, searchQuery, statusFilter]
  );

  return {
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    filterCounts,
    filteredStudents,
  };
}
