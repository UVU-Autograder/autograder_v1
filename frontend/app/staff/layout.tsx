import { ViewProvider } from "@/lib/view-context";

export default function StaffLayout({ children }: { children: React.ReactNode }) {
    return <ViewProvider mode="staff">{children}</ViewProvider>;
}