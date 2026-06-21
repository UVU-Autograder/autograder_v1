import { ViewProvider } from "@/lib/view-context";

export default function SandboxLayout({ children }: { children: React.ReactNode }) {
    return <ViewProvider mode="sandbox">{children}</ViewProvider>;
}