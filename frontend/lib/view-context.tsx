"use client";

import { createContext, useContext } from "react";

type ViewMode = "sandbox" | "staff";

const ViewContext = createContext<ViewMode | null>(null);

export function ViewProvider({mode, children}: {mode: ViewMode, children: React.ReactNode}) {
    return (
        <ViewContext.Provider value={mode}>
            {children}
        </ViewContext.Provider>
    )
}

export function useViewMode() {
    const context = useContext(ViewContext);
    if (!context) {
        throw new Error("useViewMode must be used within a ViewProvider");
    }
    return context;
}

export function useBasePath() {
    return `/${useViewMode()}`;
}