const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function getBaseUrl(): string {
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL;
}

function resolveUrl(path: string): string {
    if (path.startsWith("http://") || path.startsWith("https://")) {
        return path;
    }

    const base = getBaseUrl().replace(/\/$/, "");
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${base}${normalizedPath}`;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(resolveUrl(path), {
        ...init,
        headers: {
            'content-type': 'application/json',
            ...init?.headers,
        }
    });

    if (!response.ok) {
        throw new Error(`API request failed (${response.status}): ${response.statusText}`);
    }

    return response.json() as Promise<T>;
}

export const apiClient = {
    get: <T>(path: string) => apiFetch<T>(path),
    post: <T>(path: string, body: unknown) => apiFetch<T>(path, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(path: string, body: unknown) => apiFetch<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
}