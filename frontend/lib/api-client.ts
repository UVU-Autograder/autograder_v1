let mockHandlersPromise: Promise<typeof import("./mock-handlers")> | null = null;

function getMockHandlers(): Promise<typeof import("./mock-handlers")> | null {
    if (process.env.NODE_ENV === "production" || !isMockApiEnabled()) {
        return null;
    }
    if (!mockHandlersPromise) {
        mockHandlersPromise = import("./mock-handlers");
    }
    return mockHandlersPromise;
}

const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

/** Structured fields the backend may put in an error body's ``detail`` object. */
export type ApiErrorDetail = {
    code?: string;
    message?: string;
    retry_after_seconds?: number;
    ahead?: number;
    [key: string]: unknown;
};

export class ApiError extends Error {
    status: number;
    /** Machine-readable reason from the backend ("queue_full", "ai_busy", ...), or "client_timeout"/"network_error". */
    code?: string;
    /** How long the backend suggests waiting before a retry. */
    retryAfterSeconds?: number;
    detail?: ApiErrorDetail;

    constructor(status: number, message: string, detail?: ApiErrorDetail) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.detail = detail;
        this.code = detail?.code;
        if (typeof detail?.retry_after_seconds === "number") {
            this.retryAfterSeconds = detail.retry_after_seconds;
        }
    }
}

/** Default time limits so a request that never answers cannot leave the UI stuck. */
export const REQUEST_TIMEOUT_MS = 20_000;
export const UPLOAD_TIMEOUT_MS = 90_000;
/** Above the backend's worst case for AI feedback: up to ~20 s queued + 30 s generating + one 30 s retry. */
export const AI_TIMEOUT_MS = 120_000;

export function isMockApiEnabled(): boolean {
    if (process.env.NODE_ENV === "production") {
        return false;
    }
    if (typeof window !== "undefined") {
        try {
            const stored = window.sessionStorage?.getItem("mock_api") || window.localStorage?.getItem("mock_api");
            if (stored === "false") return false;
            if (stored === "true") return true;
        } catch {
            // Ignore storage access errors in restricted browser contexts
        }
    }
    return process.env.NEXT_PUBLIC_MOCK_API !== "false";
}

function getBaseUrl(): string {
    const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (typeof window !== "undefined" && window.location.hostname) {
        // An https API on another host (e.g. the Vercel frontend calling the VPN-only API) wins over same-origin /api.
        if (configured?.startsWith("https://") && new URL(configured).host !== window.location.host) {
            return configured;
        }
        if (!window.location.port || window.location.port === "80" || window.location.port === "443") {
            return `${window.location.protocol}//${window.location.hostname}/api`;
        }
        const hasCustomConfig = configured && !configured.includes("localhost") && !configured.includes("127.0.0.1");
        if (hasCustomConfig) {
            return configured;
        }
        const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
        if (!isLocalHost) {
            return `${window.location.protocol}//${window.location.hostname}:8000`;
        }
    }
    return configured ?? DEFAULT_BASE_URL;
}

export function resolveUrl(path: string): string {
    if (path.startsWith("http://") || path.startsWith("https://")) {
        return path;
    }

    const base = getBaseUrl().replace(/\/$/, "");
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${base}${normalizedPath}`;
}

type ApiFetchOptions = {
    headers?: Record<string, string>;
    /** Abort after this many milliseconds (default REQUEST_TIMEOUT_MS). */
    timeoutMs?: number;
};

async function parseError(response: Response): Promise<{ message: string; detail?: ApiErrorDetail }> {
    try {
        const body = (await response.json()) as { detail?: unknown };
        if (typeof body.detail === "string") {
            return { message: body.detail };
        }
        if (body.detail && typeof body.detail === "object" && !Array.isArray(body.detail)) {
            const detail = body.detail as ApiErrorDetail;
            return { message: typeof detail.message === "string" ? detail.message : response.statusText, detail };
        }
    } catch {
        // Fall back to status text below.
    }
    return { message: response.statusText };
}

async function parseErrorMessage(response: Response): Promise<string> {
    return (await parseError(response)).message;
}

/** fetch with a time limit; aborts and network failures become ApiErrors with a code. */
export async function fetchWithTimeout(
    url: string,
    init: RequestInit = {},
    timeoutMs: number = REQUEST_TIMEOUT_MS,
): Promise<Response> {
    const signal = typeof AbortSignal !== "undefined" && "timeout" in AbortSignal
        ? AbortSignal.timeout(timeoutMs)
        : undefined;
    try {
        return await fetch(url, signal ? { ...init, signal } : init);
    } catch (err) {
        if (err instanceof DOMException && (err.name === "TimeoutError" || err.name === "AbortError")) {
            throw new ApiError(0, "The server took too long to answer. Please try again.", { code: "client_timeout" });
        }
        throw new ApiError(0, "Could not reach the server. Check your connection and try again.", { code: "network_error" });
    }
}

function handleResponseError(response: Response, path: string): void {
    if (typeof window === "undefined") return;
    if (response.status === 410) {
        window.dispatchEvent(new CustomEvent("official-review-expired", { detail: path }));
    } else if (response.status === 401 && !isMockApiEnabled()) {
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
        localStorage.removeItem("lastActivity");
        window.dispatchEvent(new Event("unauthorized-api-call"));
    }
}

function getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token") || sessionStorage.getItem("token");
}

function updateStoredToken(response: Response) {
    const refreshToken = response.headers.get("x-refresh-token");
    if (refreshToken && typeof window !== "undefined") {
        if (localStorage.getItem("token")) {
            localStorage.setItem("token", refreshToken);
        } else if (sessionStorage.getItem("token")) {
            sessionStorage.setItem("token", refreshToken);
        }
    }
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

    if (process.env.NODE_ENV !== "production" && isMockApiEnabled()) {
        const mockHandlers = await getMockHandlers();
        if (mockHandlers) {
            const mockResult = await mockHandlers.handleMockRequest<T>(path, init);
            if (mockResult) {
                updateStoredToken(mockResult.response);
                return mockResult;
            }
            throw new ApiError(404, `Mock endpoint not implemented: ${(init?.method || "GET").toUpperCase()} ${path}`);
        }
    }

    const { timeoutMs, ...requestInit } = init ?? {};
    const response = await fetchWithTimeout(
        resolveUrl(path),
        { ...requestInit, headers },
        timeoutMs ?? REQUEST_TIMEOUT_MS,
    );

    if (!response.ok) {
        const { message, detail } = await parseError(response);
        handleResponseError(response, path);
        throw new ApiError(response.status, message, detail);
    }

    if (response.status === 204) {
        updateStoredToken(response);
        return { data: undefined as T, response };
    }

    updateStoredToken(response);
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        return {
            data: (await response.json()) as T,
            response,
        };
    }

    const text = await response.text();
    try {
        return {
            data: JSON.parse(text) as T,
            response,
        };
    } catch {
        return {
            data: text as unknown as T,
            response,
        };
    }
}

export const apiClient = {
    get: <T>(path: string, options?: ApiFetchOptions) =>
        apiFetch<T>(path, { method: "GET", headers: options?.headers, timeoutMs: options?.timeoutMs }).then((result) => result.data),

    getText: (path: string, options?: ApiFetchOptions): Promise<string> =>
        apiFetch<string>(path, { method: "GET", headers: options?.headers }).then((res) => String(res.data)),

    post: <T>(path: string, body: unknown, options?: ApiFetchOptions) =>
        apiFetch<T>(path, {
            method: "POST",
            body: JSON.stringify(body),
            headers: options?.headers,
            timeoutMs: options?.timeoutMs,
        }).then((result) => result.data),

    postForm: <T>(path: string, formData: FormData, options?: ApiFetchOptions) =>
        apiFetch<T>(path, {
            method: "POST",
            body: formData,
            headers: options?.headers,
            timeoutMs: options?.timeoutMs ?? UPLOAD_TIMEOUT_MS,
        }),

    put: <T>(path: string, body: unknown, options?: ApiFetchOptions) =>
        apiFetch<T>(path, {
            method: "PUT",
            body: JSON.stringify(body),
            headers: options?.headers,
        }).then((result) => result.data),

    delete: <T>(path: string, options?: ApiFetchOptions) =>
        apiFetch<T>(path, { method: "DELETE", headers: options?.headers }).then((result) => result.data),

    download: async (path: string, filename: string, options?: ApiFetchOptions): Promise<void> => {
        if (process.env.NODE_ENV !== "production" && isMockApiEnabled()) {
            const mockHandlers = await getMockHandlers();
            if (mockHandlers) {
                const blob = await mockHandlers.handleMockDownload(path);
                if (blob) {
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                    return;
                }
            }
        }

        const headers = new Headers(options?.headers);
        const token = getAuthToken();
        if (token && !headers.has("authorization")) {
            headers.set("authorization", `Bearer ${token}`);
        }

        const response = await fetch(resolveUrl(path), { method: "GET", headers });
        if (!response.ok) {
            const message = await parseErrorMessage(response);
            handleResponseError(response, path);
            throw new ApiError(response.status, message);
        }

        updateStoredToken(response);

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    },
};
