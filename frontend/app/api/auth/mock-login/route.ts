import { NextResponse } from 'next/server';
import { updateMockSession } from '@/lib/mocks/session';

export async function POST(request: Request) {
  const body = await request.json();
  const { email, display_name } = body;

  if (!email) {
    return NextResponse.json({ error: 'Email is required' }, { status: 400 });
  }

  // Mock role assignment based on email for demo purposes
  let role: 'admin' | 'instructor' | 'IA' = 'instructor';
  if (email.includes('admin')) role = 'admin';
  if (email.includes('ia')) role = 'IA';

  await updateMockSession((state) => ({
    ...state,
    user: { email, role },
  }));

  return NextResponse.json({
    access_token: 'mock-jwt-token',
    token_type: 'bearer',
    email,
    display_name: display_name || email,
  });
}
