import { cookies } from 'next/headers';

export interface MockSessionState {
  user?: {
    email: string;
    role: 'admin' | 'instructor' | 'IA';
  };
  sandboxSessionToken?: string;
  uploadCount: number;
  lastUploadTimestamp?: number;
  runs: Record<string, {
    state: 'queue' | 'run' | 'complete' | 'failure';
    profile: 'PERFECT' | 'PARTIAL' | 'FAIL';
    startTime: number;
  }>;
}

const SESSION_COOKIE_NAME = 'autograder_mock_session';

export async function getMockSession(): Promise<MockSessionState> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);
  
  if (!sessionCookie) {
    return {
      uploadCount: 0,
      runs: {},
    };
  }

  try {
    return JSON.parse(sessionCookie.value);
  } catch (e) {
    return { uploadCount: 0, runs: {} };
  }
}

export async function setMockSession(state: MockSessionState) {
  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE_NAME, JSON.stringify(state), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 3600 * 24, // 24 hours
  });
}

export async function updateMockSession(updateFn: (state: MockSessionState) => MockSessionState) {
  const currentState = await getMockSession();
  const newState = updateFn(currentState);
  await setMockSession(newState);
  return newState;
}
