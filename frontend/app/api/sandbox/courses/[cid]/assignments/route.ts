import { NextResponse } from 'next/server';
import { MOCK_ASSIGNMENTS } from '@/lib/mocks/data';

export async function GET(_request: Request, { params }: { params: Promise<{ cid: string }> }) {
  const { cid } = await params;
  const assignments = MOCK_ASSIGNMENTS[cid];

  if (!assignments) {
    return NextResponse.json({ error: 'Course not found' }, { status: 404 });
  }

  return NextResponse.json({
    course_id: cid,
    assignments: assignments,
  });
}
