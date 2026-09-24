import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { getRequestOrigin } from "@/lib/oauth-pkce";

export async function GET(request: Request) {
    const origin = getRequestOrigin(request);
    const url = new URL(request.url);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    const oauthError = url.searchParams.get("error");
    const errorDescription = url.searchParams.get("error_description");

    if (oauthError) {
        return NextResponse.redirect(
            new URL(`/staff/login?error=${encodeURIComponent(errorDescription || oauthError)}`, origin)
        );
    }

    if (!code || !state) {
        return NextResponse.redirect(
            new URL("/staff/login?error=missing_code_or_state", origin)
        );
    }

    const cookieStore = await cookies();
    const savedState = cookieStore.get("oauth_state")?.value;
    const codeVerifier = cookieStore.get("oauth_verifier")?.value;

    cookieStore.delete("oauth_state");
    cookieStore.delete("oauth_verifier");

    if (!savedState || savedState !== state) {
        return NextResponse.redirect(
            new URL("/staff/login?error=invalid_oauth_state", origin)
        );
    }

    const clientId = process.env.AZURE_AD_CLIENT_ID;
    const clientSecret = process.env.AZURE_AD_CLIENT_SECRET;
    const tenantId = process.env.AZURE_AD_TENANT_ID || "common";

    if (!clientId) {
        return NextResponse.redirect(
            new URL("/staff/login?error=missing_azure_credentials", origin)
        );
    }

    // 1. Exchange code for Microsoft ID token
    const tokenUrl = `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/token`;
    const tokenParams = new URLSearchParams({
        client_id: clientId,
        grant_type: "authorization_code",
        code,
        redirect_uri: `${origin}/api/auth/microsoft/callback`,
    });

    if (codeVerifier) {
        tokenParams.set("code_verifier", codeVerifier);
    }
    if (clientSecret) {
        tokenParams.set("client_secret", clientSecret);
    }

    let tokenData: { id_token?: string; error?: string; error_description?: string };
    try {
        const tokenRes = await fetch(tokenUrl, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: tokenParams.toString(),
        });
        tokenData = await tokenRes.json();
        if (!tokenRes.ok || !tokenData.id_token) {
            return NextResponse.redirect(
                new URL(
                    `/staff/login?error=${encodeURIComponent(tokenData.error_description || "Failed to exchange Microsoft token")}`,
                    origin
                )
            );
        }
    } catch {
        return NextResponse.redirect(
            new URL("/staff/login?error=microsoft_token_exchange_failed", origin)
        );
    }

    // 2. Exchange Microsoft ID token with FastAPI backend
    const backendBase =
        process.env.INTERNAL_BACKEND_URL ||
        process.env.NEXT_PUBLIC_API_BASE_URL ||
        "http://127.0.0.1:8000";

    const backendEndpoint = `${backendBase.replace(/\/$/, "")}/auth/microsoft-login`;

    try {
        const backendRes = await fetch(backendEndpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_token: tokenData.id_token }),
        });

        if (!backendRes.ok) {
            const errBody = await backendRes.json().catch(() => ({}));
            const detail =
                errBody.detail ||
                (backendRes.status === 403
                    ? "Account pending staff authorization"
                    : "Backend authentication failed");
            return NextResponse.redirect(
                new URL(`/staff/login?error=${encodeURIComponent(detail)}`, origin)
            );
        }

        const authResult = (await backendRes.json()) as {
            access_token: string;
            email: string;
            roles: string[];
            display_name: string | null;
        };

        const isSecure = origin.startsWith("https://");
        const handoffPayload = {
            token: authResult.access_token,
            email: authResult.email,
            roles: authResult.roles || [],
            displayName: authResult.display_name || "",
        };

        cookieStore.set("auth_handoff", JSON.stringify(handoffPayload), {
            httpOnly: false,
            secure: isSecure,
            sameSite: "lax",
            maxAge: 60, // 60 seconds handoff window
            path: "/",
        });

        return NextResponse.redirect(new URL("/staff/login", origin));
    } catch {
        return NextResponse.redirect(
            new URL("/staff/login?error=backend_connection_failed", origin)
        );
    }
}
