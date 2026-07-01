import { NextResponse } from 'next/server';
import { MOCK_COURSES, MOCK_ASSIGNMENTS } from '@/lib/mocks/data';

export async function GET() {
  return NextResponse.json({ courses: MOCK_COURSES });
}
