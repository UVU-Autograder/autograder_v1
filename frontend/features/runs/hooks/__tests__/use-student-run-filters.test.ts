import { renderHook, act } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useStudentRunFilters } from '../use-student-run-filters';
import type { StudentRunDetail } from '@/features/runs/types';

const mockStudents: StudentRunDetail[] = [
  {
    canvas_id: '101',
    student_name: 'Alice Smith',
    status: 'success',
    score: 100,
    max_score: 100,
    bundle_files: ['main.py'],
    bundle_file_count: 1,
    feedback_preview: 'All tests passed',
    feedback_html: '<p>All tests passed</p>',
    automated_score: 90,
    automated_max_score: 90,
    automated_results: [],
    manual_results: {
      visual: { label: 'Visual Check', points: 10, score: 10, comments: 'Good' },
    },
    overall_comment: '',
  },
  {
    canvas_id: '102',
    student_name: 'Bob Jones',
    status: 'success',
    score: 80,
    max_score: 100,
    bundle_files: ['main.py'],
    bundle_file_count: 1,
    feedback_preview: 'Partial pass',
    feedback_html: '<p>Partial pass</p>',
    automated_score: 80,
    automated_max_score: 90,
    automated_results: [],
    manual_results: {
      visual: { label: 'Visual Check', points: 10, score: null, comments: '' },
    },
    overall_comment: '',
  },
  {
    canvas_id: '103',
    student_name: 'Charlie Brown',
    status: 'failure',
    score: 0,
    max_score: 100,
    bundle_files: ['main.py'],
    bundle_file_count: 1,
    feedback_preview: 'Syntax error',
    feedback_html: '<p>Syntax error</p>',
    automated_score: 0,
    automated_max_score: 90,
    automated_results: [],
    manual_results: {},
    overall_comment: '',
  },
];

describe('useStudentRunFilters', () => {
  it('computes initial filter counts accurately', () => {
    const { result } = renderHook(() => useStudentRunFilters(mockStudents));

    expect(result.current.filterCounts.all).toBe(3);
    expect(result.current.filterCounts.graded).toBe(2); // Alice and Charlie (no ungraded manual items)
    expect(result.current.filterCounts.ungraded).toBe(1); // Bob (visual score is null)
    expect(result.current.filterCounts.failed).toBe(1); // Charlie (status: failure)
    expect(result.current.filteredStudents.length).toBe(3);
  });

  it('filters students by search query across name and canvas ID', () => {
    const { result } = renderHook(() => useStudentRunFilters(mockStudents));

    act(() => {
      result.current.setSearchQuery('Alice');
    });

    expect(result.current.filteredStudents.length).toBe(1);
    expect(result.current.filteredStudents[0].canvas_id).toBe('101');

    act(() => {
      result.current.setSearchQuery('103');
    });

    expect(result.current.filteredStudents.length).toBe(1);
    expect(result.current.filteredStudents[0].student_name).toBe('Charlie Brown');
  });

  it('filters students by status filter facet', () => {
    const { result } = renderHook(() => useStudentRunFilters(mockStudents));

    act(() => {
      result.current.setStatusFilter('ungraded');
    });

    expect(result.current.filteredStudents.length).toBe(1);
    expect(result.current.filteredStudents[0].canvas_id).toBe('102');

    act(() => {
      result.current.setStatusFilter('failed');
    });

    expect(result.current.filteredStudents.length).toBe(1);
    expect(result.current.filteredStudents[0].canvas_id).toBe('103');
  });
});
