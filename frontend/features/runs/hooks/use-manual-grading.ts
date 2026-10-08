import { useState, useMemo } from 'react';
import { apiClient } from '@/lib/api-client';
import { staffRunManualGradesPath } from '@/features/staff/api';
import type {
  RunDetailsResponse,
  ManualGradeSaveResponse,
  StudentRunDetail,
} from '@/features/runs/types';

export interface UseManualGradingOptions {
  courseId: string;
  assignmentId: string;
  runId: string;
  details: RunDetailsResponse | null;
  setDetails: (details: RunDetailsResponse | null) => void;
}

export function useManualGrading({
  courseId,
  assignmentId,
  runId,
  details,
  setDetails,
}: UseManualGradingOptions) {
  const [selectedCanvasId, setSelectedCanvasId] = useState<string | null>(null);
  const [isInspectOpen, setIsInspectOpen] = useState(false);
  const [isSavingGrades, setIsSavingGrades] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedStudent = useMemo(
    () =>
      details?.students.find(
        (student) => student.canvas_id === selectedCanvasId
      ) ?? null,
    [details, selectedCanvasId]
  );

  const handleInspectStudent = (student: StudentRunDetail) => {
    setSelectedCanvasId(student.canvas_id);
    setIsInspectOpen(true);
  };

  const handleInspectOpenChange = (open: boolean) => {
    setIsInspectOpen(open);
    if (!open) {
      setSelectedCanvasId(null);
    }
  };

  const handleSaveManualGrades = async (
    canvasId: string,
    grades: Record<string, { score: number | null; comments: string }>,
    overallComment: string,
    saveAndNext = false
  ) => {
    if (!details) return;
    setIsSavingGrades(true);
    try {
      const updatedStudent = await apiClient.post<ManualGradeSaveResponse>(
        staffRunManualGradesPath(courseId, assignmentId, runId, canvasId),
        {
          grades,
          overall_comment: overallComment,
        }
      );
      const updatedStudents = details.students.map((student) =>
        student.canvas_id === canvasId ? updatedStudent : student
      );
      setDetails({
        ...details,
        ...updatedStudent.manual_progress,
        students: updatedStudents,
      });
      setSuccess(
        Object.keys(grades).length > 0
          ? 'Grades and feedback saved.'
          : 'Feedback saved.'
      );
      setTimeout(() => setSuccess(null), 3000);

      if (saveAndNext) {
        const currentIndex = updatedStudents.findIndex(
          (student) => student.canvas_id === canvasId
        );
        const remainingQueue = [
          ...updatedStudents.slice(currentIndex + 1),
          ...updatedStudents.slice(0, currentIndex),
        ];
        const nextUngraded = remainingQueue.find((student) =>
          Object.values(student.manual_results).some(
            (item) => item.score === null
          )
        );
        if (nextUngraded) {
          setSelectedCanvasId(nextUngraded.canvas_id);
        } else {
          setIsInspectOpen(false);
          setSelectedCanvasId(null);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to save manual grades.'
      );
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsSavingGrades(false);
    }
  };

  return {
    selectedCanvasId,
    setSelectedCanvasId,
    selectedStudent,
    isInspectOpen,
    setIsInspectOpen,
    isSavingGrades,
    success,
    setSuccess,
    error,
    setError,
    handleInspectStudent,
    handleInspectOpenChange,
    handleSaveManualGrades,
  };
}
