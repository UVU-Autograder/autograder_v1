"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon, ShieldAlertIcon, PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
    loadData();
  }, []);

  // Fetch sections when course selection changes in the form
  useEffect(() => {
    if (selectedCourseId === "none") {
      setSections([]);
      setSelectedSectionId("none");
      return;
    }

    getCourseSections(Number(selectedCourseId))
      .then((data) => {
        setSections(data.filter(s => s.is_active));
        setSelectedSectionId("none");
      })
      .catch((err) => console.error("Failed to load sections", err));
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
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="animate-pulse font-medium text-slate-500">Loading staff access data...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
        <Link href="/staff/admin">
          <ArrowLeftIcon className="mr-1 size-4" />
          Back to admin
        </Link>
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Staff Access Management</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage administrative, instructor, and IA access roles</p>
        </div>
        <Button onClick={openGrantDialog}>
          <PlusIcon className="mr-1 size-4" /> Grant Access
        </Button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 flex items-start gap-2">
          <ShieldAlertIcon className="size-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Staff Access Control List</CardTitle>
          <CardDescription>Active role grants scoped to courses and sections</CardDescription>
        </CardHeader>
        <CardContent>
          {accessList.length === 0 ? (
            <p className="text-slate-400 text-center py-6 text-sm">No staff access permissions found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500 font-semibold">
                    <th className="py-2.5">User</th>
                    <th className="py-2.5">Role</th>
                    <th className="py-2.5">Course</th>
                    <th className="py-2.5">Section</th>
                    <th className="py-2.5">Status</th>
                    <th className="py-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {accessList.map((access) => (
                    <tr key={access.id} className={!access.is_active ? "opacity-50" : ""}>
                      <td className="py-3 font-medium text-slate-800">
                        <div>{access.user_name || "Guest"}</div>
                        <div className="text-xs text-slate-400 font-normal">{access.user_email}</div>
                      </td>
                      <td className="py-3">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                          access.role_name === 'admin' 
                            ? 'bg-purple-50 text-purple-700' 
                            : access.role_name === 'instructor' 
                              ? 'bg-blue-50 text-blue-700' 
                              : 'bg-indigo-50 text-indigo-700'
                        }`}>
                          {access.role_name}
                        </span>
                      </td>
                      <td className="py-3 uppercase font-semibold text-slate-600">
                        {access.course_code || "All"}
                      </td>
                      <td className="py-3 text-slate-500 font-mono text-xs">
                        {access.section_crn || "All"}
                      </td>
                      <td className="py-3">
                        <span className={`text-xs ${access.is_active ? 'text-green-600 font-semibold' : 'text-slate-400'}`}>
                          {access.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        {access.is_active && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 h-8"
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
        </CardContent>
      </Card>

      {/* --- GRANT ACCESS DIALOG --- */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Grant Staff Access</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleGrantSubmit} className="space-y-4 py-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">UVU Email Address</label>
              <Input
                type="email"
                placeholder="e.g., green.scholar@uvu.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Display Name (optional)</label>
              <Input
                placeholder="e.g., Professor Green"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">System Role</label>
              <select
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
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
                  <label className="text-xs font-semibold text-slate-500 uppercase">Course Scope</label>
                  <select
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
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
                    <label className="text-xs font-semibold text-slate-500 uppercase">Section Scope</label>
                    <select
                      className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
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

            {formError && <p className="text-xs text-red-500 font-medium">{formError}</p>}

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
