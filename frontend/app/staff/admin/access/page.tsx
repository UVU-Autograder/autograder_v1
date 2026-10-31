"use client";

import { useState, useEffect } from "react";
import { PlusIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageEmpty, PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  getAdminAccessList,
  grantAdminAccess,
  revokeAdminAccess,
  getAdminCourses,
  getCourseSections,
  StaffAccessRecord,
} from "@/features/courses/api";
import { CourseAdminDetail } from "@/features/courses/types";

type SectionSummary = {
  id: number;
  course_id: number;
  crn: string;
  is_active: boolean;
};

export default function AccessPage() {
  const [accessList, setAccessList] = useState<StaffAccessRecord[]>([]);
  const [courses, setCourses] = useState<CourseAdminDetail[]>([]);
  const [sections, setSections] = useState<SectionSummary[]>([]);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog state
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form fields
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [roleName, setRoleName] = useState("instructor");
  const [selectedCourseId, setSelectedCourseId] = useState<string>("none");
  const [selectedSectionId, setSelectedSectionId] = useState<string>("none");

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const access = await getAdminAccessList();
      setAccessList(access);
      
      const courseList = await getAdminCourses();
      setCourses(courseList.filter(c => c.is_active));
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load access details.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void Promise.resolve().then(loadData);
  }, []);

  // Fetch sections when course selection changes in the form
  useEffect(() => {
    void Promise.resolve().then(async () => {
      if (selectedCourseId === "none") {
        setSections([]);
        setSelectedSectionId("none");
        return;
      }

      try {
        const data = await getCourseSections(Number(selectedCourseId));
        setSections(data.filter(s => s.is_active));
        setSelectedSectionId("none");
      } catch (err) {
        console.error("Failed to load sections", err);
      }
    });
  }, [selectedCourseId]);

  const openGrantDialog = () => {
    setEmail("");
    setDisplayName("");
    setRoleName("instructor");
    setSelectedCourseId("none");
    setSelectedSectionId("none");
    setFormError(null);
    setIsOpen(true);
  };

  const handleGrantSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setFormError("Email address is required.");
      return;
    }
    if (!email.trim().toLowerCase().endsWith("@uvu.edu")) {
      setFormError("Staff access is restricted to @uvu.edu addresses.");
      return;
    }

    setFormError(null);
    setIsSubmitting(true);
    try {
      await grantAdminAccess({
        email: email.trim().toLowerCase(),
        display_name: displayName.trim() || null,
        role_name: roleName,
        course_id: selectedCourseId === "none" ? null : Number(selectedCourseId),
        section_id: selectedSectionId === "none" ? null : Number(selectedSectionId),
      });

      setIsOpen(false);
      loadData();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to grant staff access.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevoke = async (accessId: number) => {
    if (!confirm("Are you sure you want to revoke this staff access scope?")) {
      return;
    }
    try {
      await revokeAdminAccess(accessId);
      loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to revoke access.");
    }
  };

  if (isLoading) {
    return <PageLoading className="h-screen">Loading staff access data...</PageLoading>;
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8 pb-12">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: "Admin", href: "/staff/admin" },
          { label: "Access" },
        ]}
      />

      <AdminPageHeader
        title="Access"
        description="Grant and revoke instructor, IA, and admin roles."
        actions={
          <Button onClick={openGrantDialog}>
            <PlusIcon className="mr-1 size-4" /> Grant access
          </Button>
        }
      />

      {error && (
        <div className="mb-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {accessList.length === 0 ? (
        <PageEmpty>No staff access grants yet.</PageEmpty>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="py-2 font-medium">User</th>
                <th className="py-2 font-medium">Role</th>
                <th className="py-2 font-medium">Course</th>
                <th className="py-2 font-medium">Section</th>
                <th className="py-2 font-medium">Status</th>
                <th className="py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {accessList.map((access) => (
                <tr key={access.id} className={!access.is_active ? "opacity-50" : ""}>
                  <td className="py-3 text-foreground">
                    <div className="font-medium">{access.user_name || "Guest"}</div>
                    <div className="text-xs text-muted-foreground">{access.user_email}</div>
                  </td>
                  <td className="py-3 text-foreground capitalize">{access.role_name}</td>
                  <td className="py-3 text-xs font-semibold uppercase tracking-wider text-primary">
                    {access.course_code || "All"}
                  </td>
                  <td className="py-3 text-muted-foreground text-xs">
                    {access.section_crn || "All"}
                  </td>
                  <td className="py-3 text-xs text-muted-foreground">
                    {access.is_active ? "Active" : "Inactive"}
                  </td>
                  <td className="py-3 text-right">
                    {access.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 text-destructive hover:bg-destructive/10"
                        onClick={() => handleRevoke(access.id)}
                      >
                        Revoke
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* --- GRANT ACCESS DIALOG --- */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Grant Staff Access</DialogTitle>
            <DialogDescription>
              Enter the UVU email address and assign a course-wide or section-wide role.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleGrantSubmit} className="space-y-4 py-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">UVU Email Address</label>
              <Input
                type="email"
                placeholder="e.g., green.scholar@uvu.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Display Name (optional)</label>
              <Input
                placeholder="e.g., Professor Green"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">System Role</label>
              <select
                className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
              >
                <option value="instructor">Instructor (Course/Section owner)</option>
                <option value="IA">Instructional Assistant (Section assistant)</option>
                <option value="admin">Administrator (Global scopes)</option>
              </select>
            </div>

            {roleName !== "admin" && (
              <>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Course Scope</label>
                  <select
                    className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    value={selectedCourseId}
                    onChange={(e) => setSelectedCourseId(e.target.value)}
                  >
                    <option value="none">Select course...</option>
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.title} ({c.code})
                      </option>
                    ))}
                  </select>
                </div>

                {selectedCourseId !== "none" && (
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Section Scope</label>
                    <select
                      className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      value={selectedSectionId}
                      onChange={(e) => setSelectedSectionId(e.target.value)}
                    >
                      <option value="none">All Sections (Course-wide)</option>
                      {sections.map((s) => (
                        <option key={s.id} value={s.id}>
                          CRN {s.crn}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </>
            )}

            {formError && <p className="text-xs text-destructive font-medium">{formError}</p>}

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Granting..." : "Grant Access"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
