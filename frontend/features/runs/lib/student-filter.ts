import { StudentRunDetail, StatusFilter, ScoreBucket } from "../types";

export function hasUngradedManualItems(student: StudentRunDetail): boolean {
  return Object.values(student.manual_results ?? {}).some(
    (item) => item.score === null,
  );
}

export function sortStudentsByName(students: StudentRunDetail[]): StudentRunDetail[] {
  return [...students].sort((a, b) =>
    a.student_name.localeCompare(b.student_name),
  );
}

export function formatBundleSummary(student: StudentRunDetail): string {
  const count = student.bundle_file_count ?? student.bundle_files?.length ?? 0;
  if (count === 0) {
    return "No submission files prepared";
  }
  return `${count} file${count === 1 ? "" : "s"}`;
}

export function filterStudents(
  students: StudentRunDetail[],
  query: string,
  filter: StatusFilter,
): StudentRunDetail[] {
  const normalizedQuery = query.trim().toLowerCase();

  return students.filter((student) => {
    if (normalizedQuery) {
      const nameMatch = student.student_name.toLowerCase().includes(normalizedQuery);
      const idMatch = student.canvas_id.toLowerCase().includes(normalizedQuery);
      if (!nameMatch && !idMatch) return false;
    }

    const manualCount = Object.keys(student.manual_results ?? {}).length;
    if (filter === "ungraded") {
      return manualCount > 0 && hasUngradedManualItems(student);
    }
    if (filter === "graded") {
      return manualCount === 0 || !hasUngradedManualItems(student);
    }
    if (filter === "failed") {
      return student.status === "failure";
    }
    return true;
  });
}

export function buildScoreHistogram(students: StudentRunDetail[]): ScoreBucket[] {
  const buckets: ScoreBucket[] = Array.from({ length: 10 }, (_, i) => ({
    key: `b${i}`,
    shortLabel: i === 9 ? "90+" : `${i * 10}`,
    rangeLabel: i === 9 ? "90–100%" : `${i * 10}–${i * 10 + 9}%`,
    count: 0,
  }));

  for (const student of students) {
    const max = typeof student.max_score === "number" && !Number.isNaN(student.max_score) ? student.max_score : 0;
    const score = typeof student.score === "number" && !Number.isNaN(student.score) ? student.score : 0;
    const pct = max > 0 ? (score / max) * 100 : 0;
    const index = Math.min(9, Math.max(0, Math.floor(pct / 10)));
    buckets[index].count += 1;
  }

  return buckets;
}
