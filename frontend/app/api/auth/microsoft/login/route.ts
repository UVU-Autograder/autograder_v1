import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
    generateCodeChallenge,
    generateRandomString,
    getRequestOrigin,
} from "@/lib/oauth-pkce";

export async function GET(request: Request) {
    const clientId = process.env.AZURE_AD_CLIENT_ID;
    const tenantId = process.env.AZURE_AD_TENANT_ID || "common";

    const origin = getRequestOrigin(request);

    if (!clientId) {
        return NextResponse.redirect(
            new URL("/staff/login?error=missing_azure_credentials", origin)
        );
    }

    const state = generateRandomString(32);
    const codeVerifier = generateRandomString(64);
    const codeChallenge = await generateCodeChallenge(codeVerifier);

    const redirectUri = `${origin}/api/auth/microsoft/callback`;

    const authUrl = new URL(
        `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize`
    );
    authUrl.searchParams.set("client_id", clientId);
    authUrl.searchParams.set("response_type", "code");
    authUrl.searchParams.set("redirect_uri", redirectUri);
    authUrl.searchParams.set("response_mode", "query");
    authUrl.searchParams.set("scope", "openid profile email");
    authUrl.searchParams.set("state", state);
    authUrl.searchParams.set("code_challenge", codeChallenge);
    authUrl.searchParams.set("code_challenge_method", "S256");
    authUrl.searchParams.set("prompt", "select_account");

    const cookieStore = await cookies();
    const isSecure = origin.startsWith("https://");

    cookieStore.set("oauth_state", state, {
        httpOnly: true,
        secure: isSecure,
        sameSite: "lax",
        maxAge: 600, // 10 minutes
        path: "/",
    });

    cookieStore.set("oauth_verifier", codeVerifier, {
        httpOnly: true,
        secure: isSecure,
        sameSite: "lax",
        maxAge: 600,
        path: "/",
    });

    const requestUrl = new URL(request.url);
    const returnTo = requestUrl.searchParams.get("return_to");
    if (returnTo && returnTo.startsWith("/staff") && !returnTo.startsWith("/staff/login")) {
        cookieStore.set("auth_return_to", returnTo, {
            httpOnly: true,
            secure: isSecure,
            sameSite: "lax",
            maxAge: 600,
            path: "/",
        });
    }

    return NextResponse.redirect(authUrl.toString());
}
