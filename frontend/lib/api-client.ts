const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

export class ApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

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

type ApiFetchOptions = {
    headers?: Record<string, string>;
};

async function parseErrorMessage(response: Response): Promise<string> {
    try {
        const body = (await response.json()) as { detail?: string };
        if (typeof body.detail === "string") {
            return body.detail;
        }
    } catch {
        // Fall back to status text below.
    }
    return response.statusText;
}

function getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token") || sessionStorage.getItem("token");
}

async function apiFetch<T>(
    path: string,
    init?: RequestInit & ApiFetchOptions
): Promise<{ data: T; response: Response }> {
    const headers = new Headers(init?.headers);
    const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;

    if (!isFormData && !headers.has("content-type") && init?.body !== undefined) {
        headers.set("content-type", "application/json");
    }

    const token = getAuthToken();
    if (token && !headers.has("authorization")) {
        headers.set("authorization", `Bearer ${token}`);
    }

    const response = await fetch(resolveUrl(path), {
        ...init,
        headers,
    });

    if (!response.ok) {
        const message = await parseErrorMessage(response);
        throw new ApiError(response.status, message);
    }

    if (response.status === 204) {
        return { data: undefined as T, response };
    }

    return {
        data: (await response.json()) as T,
        response,
    };
}

export const apiClient = {
    get: <T>(path: string, options?: ApiFetchOptions) =>
        apiFetch<T>(path, { method: "GET", headers: options?.headers }).then((result) => result.data),

    post: <T>(path: string, body: unknown, options?: ApiFetchOptions) =>
        apiFetch<T>(path, {
            method: "POST",
            body: JSON.stringify(body),
            headers: options?.headers,
        }).then((result) => result.data),

    postForm: <T>(path: string, formData: FormData, options?: ApiFetchOptions) =>
        apiFetch<T>(path, {
            method: "POST",
            body: formData,
            headers: options?.headers,
        }),

    put: <T>(path: string, body: unknown, options?: ApiFetchOptions) =>
        apiFetch<T>(path, {
            method: "PUT",
            body: JSON.stringify(body),
            headers: options?.headers,
        }).then((result) => result.data),

    delete: <T>(path: string, options?: ApiFetchOptions) =>
        apiFetch<T>(path, { method: "DELETE", headers: options?.headers }).then((result) => result.data),
};
