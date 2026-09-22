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
    const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (typeof window !== "undefined" && window.location.hostname) {
        const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
        if (!isLocalHost && (!configured || configured.includes("localhost") || configured.includes("127.0.0.1"))) {
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

    const response = await fetch(resolveUrl(path), {
        ...init,
        headers,
    });

    if (!response.ok) {
        const message = await parseErrorMessage(response);
        if (response.status === 410 && typeof window !== "undefined") {
            window.dispatchEvent(new CustomEvent("official-review-expired", { detail: path }));
        }
        if (typeof window !== "undefined" && (response.status === 401 || response.status === 403)) {
            localStorage.removeItem("token");
            sessionStorage.removeItem("token");
            localStorage.removeItem("lastActivity");
            window.dispatchEvent(new Event("unauthorized-api-call"));
        }
        throw new ApiError(response.status, message);
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
        apiFetch<T>(path, { method: "GET", headers: options?.headers }).then((result) => result.data),

    getText: (path: string, options?: ApiFetchOptions): Promise<string> =>
        apiFetch<string>(path, { method: "GET", headers: options?.headers }).then((res) => String(res.data)),

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

    download: async (path: string, filename: string, options?: ApiFetchOptions): Promise<void> => {
        const headers = new Headers(options?.headers);
        const token = getAuthToken();
        if (token && !headers.has("authorization")) {
            headers.set("authorization", `Bearer ${token}`);
        }

        const response = await fetch(resolveUrl(path), { method: "GET", headers });
        if (!response.ok) {
            const message = await parseErrorMessage(response);
        if (response.status === 410 && typeof window !== "undefined") {
            window.dispatchEvent(new CustomEvent("official-review-expired", { detail: path }));
        }
            if (typeof window !== "undefined" && (response.status === 401 || response.status === 403)) {
                localStorage.removeItem("token");
                sessionStorage.removeItem("token");
                localStorage.removeItem("lastActivity");
                window.dispatchEvent(new Event("unauthorized-api-call"));
            }
            throw new ApiError(response.status, message);
        }

        updateStoredToken(response);

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    },
};
