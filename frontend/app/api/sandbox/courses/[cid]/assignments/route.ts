import { NextResponse } from 'next/server';
import { MOCK_ASSIGNMENTS } from '@/lib/mocks/data';

type CourseId = keyof typeof MOCK_ASSIGNMENTS;

export async function GET(_request: Request, { params }: { params: Promise<{ cid: string }> }) {
  const { cid } = await params;

  if (!Object.hasOwn(MOCK_ASSIGNMENTS, cid)) {
    return NextResponse.json({ error: 'Course not found' }, { status: 404 });
  }

  const courseId = cid as CourseId;
  const assignments = MOCK_ASSIGNMENTS[courseId];

  return NextResponse.json({
    course_id: courseId,
    assignments: assignments,
  });
}
