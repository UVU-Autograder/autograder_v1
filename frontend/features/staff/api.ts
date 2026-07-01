/**
 * Staff-facing API helpers. Staff assignment lists intentionally reuse the
 * sandbox assignments endpoint for a student-parity view — see features/assignments/api.ts.
 */

export function staffArtifactPath(
  courseId: string,
  assignmentId: string,
  artifactKey: string
): string {
  return `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${artifactKey}`;
}

export function staffRunCsvExportPath(
  courseId: string,
  assignmentId: string,
  runId: string
): string {
  return `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/export/csv`;
}

export function staffRunFeedbackExportPath(
  courseId: string,
  assignmentId: string,
  runId: string
): string {
  return `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/export/feedback`;
}

export function staffRunStudentFilesPath(
  courseId: string,
  assignmentId: string,
  runId: string,
  canvasId: string
): string {
  return `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/students/${canvasId}/files`;
}

export function staffRunStudentFileContentPath(
  courseId: string,
  assignmentId: string,
  runId: string,
  canvasId: string,
  filepath: string
): string {
  return `${staffRunStudentFilesPath(courseId, assignmentId, runId, canvasId)}/content?filepath=${encodeURIComponent(filepath)}`;
}

export function staffRunManualGradesPath(
  courseId: string,
  assignmentId: string,
  runId: string,
  canvasId: string
): string {
  return `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/students/${canvasId}/manual-grades`;
}
