import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { CourseAdminDetail } from "@/features/courses/types";
import {
  createAdminCourse,
  updateAdminCourse,
  deleteAdminCourse,
  getAdminUsers,
} from "@/features/courses/api";

type UserSummary = {
  id: number;
  email: string;
  display_name: string | null;
  is_active: boolean;
};

export default function AllCoursesPage({
  initialCourses,
  refreshCourses,
}: {
  initialCourses: CourseAdminDetail[];
  refreshCourses: () => void;
}) {
  const [courses, setCourses] = useState<CourseAdminDetail[]>(initialCourses);
  const [users, setUsers] = useState<UserSummary[]>([]);
  
  // Dialog Open states
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // Selected course for Edit / Delete
  const [selectedCourse, setSelectedCourse] = useState<CourseAdminDetail | null>(null);

  // Form states
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [term, setTerm] = useState("");
  const [concepts, setConcepts] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [instructorId, setInstructorId] = useState<string>("none");
  const [iaId, setIaId] = useState<string>("none");

  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update local courses state when initialCourses changes
  useEffect(() => {
    setCourses(initialCourses);
  }, [initialCourses]);

  // Load user list for dropdowns when edit dialog is active
  useEffect(() => {
    getAdminUsers()
      .then((data) => setUsers(data))
      .catch((err) => console.error("Failed to load users", err));
  }, []);

  const openAddDialog = () => {
    setCode("");
    setTitle("");
    setTerm("");
    setConcepts("");
    setFormError(null);
    setIsAddOpen(true);
  };

  const openEditDialog = (course: CourseAdminDetail) => {
    setSelectedCourse(course);
    setCode(course.code);
    setTitle(course.title);
    setTerm(course.term);
    setConcepts(course.default_concepts.join(", "));
    setIsActive(course.is_active);
    setInstructorId(course.instructor_id ? String(course.instructor_id) : "none");
    setIaId(course.ia_id ? String(course.ia_id) : "none");
    setFormError(null);
    setIsEditOpen(true);
  };

  const openDeleteDialog = (course: CourseAdminDetail) => {
    setSelectedCourse(course);
    setIsDeleteOpen(true);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !title.trim() || !term.trim()) {
      setFormError("All fields except concepts are required.");
      return;
    }
    setFormError(null);
    setIsSubmitting(true);
    try {
      const conceptsList = concepts
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      await createAdminCourse({
        code: code.trim(),
        title: title.trim(),
        term: term.trim(),
        default_concepts: conceptsList,
      });

      setIsAddOpen(false);
      refreshCourses();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create course.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse) return;
    if (!code.trim() || !title.trim() || !term.trim()) {
      setFormError("Code, Title, and Term are required.");
      return;
    }
    setFormError(null);
    setIsSubmitting(true);
    try {
      const conceptsList = concepts
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      await updateAdminCourse(selectedCourse.id, {
        code: code.trim(),
        title: title.trim(),
        term: term.trim(),
        default_concepts: conceptsList,
        is_active: isActive,
        instructor_id: instructorId === "none" ? 0 : Number(instructorId),
        ia_id: iaId === "none" ? 0 : Number(iaId),
      });

      setIsEditOpen(false);
      refreshCourses();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to update course.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteSubmit = async () => {
    if (!selectedCourse) return;
    setIsSubmitting(true);
    try {
      await deleteAdminCourse(selectedCourse.id);
      setIsDeleteOpen(false);
      refreshCourses();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to deactivate course.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
        <Link href="/staff/admin">
          <ArrowLeftIcon className="mr-1 size-4" />
          Back to admin
        </Link>
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">All Courses</h1>
        <Button onClick={openAddDialog}>Add course</Button>
      </div>

      {courses.length === 0 ? (
        <p className="text-muted-foreground">No courses available yet.</p>
      ) : (
        <div className="flex w-full flex-col gap-2">
          {courses.map((course) => (
            <Card key={course.id} className={`py-3 transition-shadow hover:shadow-md ${!course.is_active ? 'opacity-60 bg-slate-50' : ''}`}>
              <CardContent className="flex items-center gap-3 py-0">
                <Link
                  href={`/staff/courses/${course.code}`}
                  className="min-w-0 flex-1"
                >
                  <div className="space-y-0.5">
                    <CardTitle className="truncate text-base flex items-center gap-2">
                      {course.title}
                      {!course.is_active && (
                        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-600 uppercase">
                          Inactive
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-slate-500">
                      <span className="font-semibold uppercase text-slate-700">{course.code}</span>
                      <span>•</span>
                      <span>{course.term}</span>
                      <span>•</span>
                      <span>
                        {course.assignment_count}{" "}
                        {course.assignment_count === 1 ? "assignment" : "assignments"}
                      </span>
                      {course.instructor_email && (
                        <>
                          <span>•</span>
                          <span className="truncate">Instructor: {course.instructor_email}</span>
                        </>
                      )}
                    </CardDescription>
                  </div>
                </Link>
                <div className="flex shrink-0 gap-2">
                  <Button variant="outline" size="sm" onClick={() => openEditDialog(course)}>
                    Edit
                  </Button>
                  {course.is_active && (
                    <Button variant="destructive" size="sm" onClick={() => openDeleteDialog(course)}>
                      Deactivate
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* --- ADD COURSE DIALOG --- */}
      <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Course</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddSubmit} className="space-y-4 py-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Course Code</label>
              <Input
                placeholder="e.g., cs1400"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Course Title</label>
              <Input
                placeholder="e.g., Fundamentals of Programming"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Term</label>
              <Input
                placeholder="e.g., Fall 2026"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Default Concepts (comma-separated)</label>
              <Input
                placeholder="e.g., variables, loops, lists"
                value={concepts}
                onChange={(e) => setConcepts(e.target.value)}
              />
            </div>

            {formError && <p className="text-xs text-red-500 font-medium">{formError}</p>}

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Course"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- EDIT COURSE DIALOG --- */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Course</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4 py-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Course Code</label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Course Title</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Term</label>
              <Input
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Default Concepts (comma-separated)</label>
              <Input
                value={concepts}
                onChange={(e) => setConcepts(e.target.value)}
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Instructor</label>
              <select
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                value={instructorId}
                onChange={(e) => setInstructorId(e.target.value)}
              >
                <option value="none">None</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} {u.display_name ? `(${u.display_name})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">IA (Teaching Assistant)</label>
              <select
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                value={iaId}
                onChange={(e) => setIaId(e.target.value)}
              >
                <option value="none">None</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} {u.display_name ? `(${u.display_name})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="edit-is-active"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded border-slate-300 text-slate-600 focus:ring-slate-500"
              />
              <label htmlFor="edit-is-active" className="text-sm font-medium text-slate-700">
                Course is active
              </label>
            </div>

            {formError && <p className="text-xs text-red-500 font-medium">{formError}</p>}

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Saving..." : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- CONFIRM DELETE DIALOG --- */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Deactivate Course</DialogTitle>
          </DialogHeader>
          <div className="py-2 text-sm text-slate-600">
            Are you sure you want to deactivate <span className="font-semibold text-slate-900">"{selectedCourse?.title}" ({selectedCourse?.code})</span>?
            This will hide the course from normal staff and sandbox views, but historical records will be preserved.
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteSubmit} disabled={isSubmitting}>
              {isSubmitting ? "Deactivating..." : "Deactivate"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
