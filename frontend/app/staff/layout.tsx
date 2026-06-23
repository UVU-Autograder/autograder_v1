import { ViewProvider } from "@/lib/view-context";
import { StaffAuthGuard } from "@/components/staff-auth-guard";

export default function StaffLayout({ children }: { children: React.ReactNode }) {
    return (
        <ViewProvider mode="staff">
            <StaffAuthGuard>{children}</StaffAuthGuard>
        </ViewProvider>
    );
}