import { useState, useEffect } from "react";
import Link from "next/link";
import { BackLink } from "@/components/back-link";
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
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { CourseAdminDetail } from "@/features/courses/types";
import {
  createAdminCourse,
  updateAdminCourse,
  deleteAdminCourse,
  getAdminUsers,
} from "@/features/courses/api";
import { getConceptsMetadata } from "@/features/assignments/api";
import type { ConceptMetadata } from "@/features/assignments/types";

type UserSummary = {
  id: number;
  email: string;
  display_name: string | null;
  is_active: boolean;
};

function DefaultConceptsPicker({
  metadata,
  selected,
  onToggle,
}: {
  metadata: Record<string, ConceptMetadata>;
  selected: string[];
  onToggle: (key: string) => void;
}) {
  const items = Object.values(metadata);
  if (items.length === 0) {
    return (
      <p className="text-xs text-muted-foreground italic">
        Loading concept catalog…
      </p>
    );
  }

  return (
    <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border border-border bg-muted/20 p-2">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {items.map((item) => {
          const checked = selected.includes(item.key);
          return (
            <label
              key={item.key}
              className={`flex cursor-pointer items-start gap-2 rounded-md border p-2.5 text-left transition-colors ${
                checked
                  ? "border-success/40 bg-success/10"
                  : "border-border bg-card hover:bg-muted/50"
              }`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(item.key)}
                className="mt-0.5 size-3.5 rounded border-input text-primary focus:ring-ring"
              />
              <span className="min-w-0 space-y-1">
                <span className="block text-xs font-semibold text-foreground uppercase">
                  {item.title}
                </span>
                {(item.syntax_patterns || []).length > 0 && (
                  <span className="flex flex-wrap gap-1">
                    {item.syntax_patterns.slice(0, 3).map((pattern) => (
                      <code
                        key={pattern}
                        className="rounded border border-border bg-background px-1 py-0.5 font-mono text-[10px] text-muted-foreground"
                      >
                        {pattern}
                      </code>
                    ))}
                  </span>
                )}
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

export default function AllCoursesPage({
  initialCourses,
  refreshCourses,
}: {
  initialCourses: CourseAdminDetail[];
  refreshCourses: () => void;
}) {
  const [courses, setCourses] = useState<CourseAdminDetail[]>(initialCourses);
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [conceptMetadata, setConceptMetadata] = useState<
    Record<string, ConceptMetadata>
  >({});

  // Keep track of the prop we synchronized to avoid useEffect setState warning
  const [prevInitialCourses, setPrevInitialCourses] = useState(initialCourses);
  if (initialCourses !== prevInitialCourses) {
    setCourses(initialCourses);
    setPrevInitialCourses(initialCourses);
  }

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
  const [concepts, setConcepts] = useState<string[]>([]);
  const [isActive, setIsActive] = useState(true);
  const [instructorId, setInstructorId] = useState<string>("none");
  const [iaId, setIaId] = useState<string>("none");

  // Email-based states for new users
  const [instructorEmail, setInstructorEmail] = useState("");
  const [instructorName, setInstructorName] = useState("");
  const [iaEmail, setIaEmail] = useState("");
  const [iaName, setIaName] = useState("");

  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    getAdminUsers()
      .then((data) => setUsers(data))
      .catch((err) => console.error("Failed to load users", err));
    getConceptsMetadata()
      .then((data) => setConceptMetadata(data))
      .catch((err) => console.error("Failed to load concept metadata", err));
  }, []);

  const toggleConcept = (key: string) => {
    setConcepts((prev) =>
      prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key],
    );
  };

  const openAddDialog = () => {
    setCode("");
    setTitle("");
    setTerm("");
    setConcepts([]);
    setInstructorId("none");
    setIaId("none");
    setInstructorEmail("");
    setInstructorName("");
    setIaEmail("");
    setIaName("");
    setFormError(null);
    setIsAddOpen(true);
  };

  const openEditDialog = (course: CourseAdminDetail) => {
    setSelectedCourse(course);
    setCode(course.code);
    setTitle(course.title);
    setTerm(course.term);
    setConcepts([...course.default_concepts]);
    setIsActive(course.is_active);
    setInstructorId(course.instructor_id ? String(course.instructor_id) : "none");
    setIaId(course.ia_id ? String(course.ia_id) : "none");
    setInstructorEmail("");
    setInstructorName("");
    setIaEmail("");
    setIaName("");
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

    if (instructorId === "custom" && (!instructorEmail.trim() || !instructorEmail.trim().toLowerCase().endsWith("@uvu.edu"))) {
      setFormError("Instructor email must be a @uvu.edu address.");
      return;
    }
    if (iaId === "custom" && (!iaEmail.trim() || !iaEmail.trim().toLowerCase().endsWith("@uvu.edu"))) {
      setFormError("IA email must be a @uvu.edu address.");
      return;
    }

    setFormError(null);
    setIsSubmitting(true);
    try {
      const payload: {
        code: string;
        title: string;
        term: string;
        default_concepts: string[];
        instructor_email?: string | null;
        instructor_name?: string | null;
        instructor_id?: number | null;
        ia_email?: string | null;
        ia_name?: string | null;
        ia_id?: number | null;
      } = {
        code: code.trim(),
        title: title.trim(),
        term: term.trim(),
        default_concepts: concepts,
      };

      if (instructorId === "custom" && instructorEmail.trim()) {
        payload.instructor_email = instructorEmail.trim().toLowerCase();
        payload.instructor_name = instructorName.trim() || null;
      } else if (instructorId !== "none" && instructorId !== "custom") {
        payload.instructor_id = Number(instructorId);
      }

      if (iaId === "custom" && iaEmail.trim()) {
        payload.ia_email = iaEmail.trim().toLowerCase();
        payload.ia_name = iaName.trim() || null;
      } else if (iaId !== "none" && iaId !== "custom") {
        payload.ia_id = Number(iaId);
      }

      await createAdminCourse(payload);

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

    if (instructorId === "custom" && (!instructorEmail.trim() || !instructorEmail.trim().toLowerCase().endsWith("@uvu.edu"))) {
      setFormError("Instructor email must be a @uvu.edu address.");
      return;
    }
    if (iaId === "custom" && (!iaEmail.trim() || !iaEmail.trim().toLowerCase().endsWith("@uvu.edu"))) {
      setFormError("IA email must be a @uvu.edu address.");
      return;
    }

    setFormError(null);
    setIsSubmitting(true);
    try {
      const payload: {
        code: string;
        title: string;
        term: string;
        default_concepts: string[];
        is_active: boolean;
        instructor_email?: string | null;
        instructor_name?: string | null;
        instructor_id?: number | null;
        ia_email?: string | null;
        ia_name?: string | null;
        ia_id?: number | null;
      } = {
        code: code.trim(),
        title: title.trim(),
        term: term.trim(),
        default_concepts: concepts,
        is_active: isActive,
      };

      if (instructorId === "custom" && instructorEmail.trim()) {
        payload.instructor_email = instructorEmail.trim().toLowerCase();
        payload.instructor_name = instructorName.trim() || null;
        payload.instructor_id = null;
      } else {
        payload.instructor_id = instructorId === "none" ? 0 : Number(instructorId);
        payload.instructor_email = "";
      }

      if (iaId === "custom" && iaEmail.trim()) {
        payload.ia_email = iaEmail.trim().toLowerCase();
        payload.ia_name = iaName.trim() || null;
        payload.ia_id = null;
      } else {
        payload.ia_id = iaId === "none" ? 0 : Number(iaId);
        payload.ia_email = "";
      }

      await updateAdminCourse(selectedCourse.id, payload);

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
      <BackLink href="/staff/admin">Back to admin</BackLink>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">All Courses</h1>
        <Button onClick={openAddDialog}>Add course</Button>
      </div>

      {courses.length === 0 ? (
        <p className="text-muted-foreground">No courses available yet.</p>
      ) : (
        <div className="flex w-full flex-col gap-2">
          {courses.map((course) => (
            <Card key={course.id} className={`py-3 transition-shadow hover:shadow-md ${!course.is_active ? 'opacity-60 bg-muted/40' : ''}`}>
              <CardContent className="flex items-center gap-3 py-0">
                <Link
                  href={`/staff/courses/${course.code}`}
                  className="min-w-0 flex-1"
                >
                  <div className="space-y-0.5">
                    <CardTitle className="truncate text-base flex items-center gap-2">
                      {course.title}
                      {!course.is_active && (
                        <span className="rounded-full bg-muted border border-border px-2 py-0.5 text-xs font-semibold text-muted-foreground uppercase">
                          Inactive
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                      <span className="font-semibold uppercase text-foreground">{course.code}</span>
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
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New Course</DialogTitle>
            <DialogDescription>
              Fill out the details below to register a new course in the system.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddSubmit} className="space-y-4 py-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Course Code</label>
              <Input
                placeholder="e.g., cs1400"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Course Title</label>
              <Input
                placeholder="e.g., Fundamentals of Programming"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Term</label>
              <Input
                placeholder="e.g., Fall 2026"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline justify-between gap-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Default Concepts
                </label>
                <span className="text-[10px] text-muted-foreground">
                  {concepts.length} selected
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Select default allowed structures for assignments in this course.
              </p>
              <DefaultConceptsPicker
                metadata={conceptMetadata}
                selected={concepts}
                onToggle={toggleConcept}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Instructor</label>
              <select
                className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={instructorId}
                onChange={(e) => setInstructorId(e.target.value)}
              >
                <option value="none">None</option>
                <option value="custom">+ Add by email...</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} {u.display_name ? `(${u.display_name})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {instructorId === "custom" && (
              <div className="border border-border bg-muted/30 rounded-md p-3 space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New Instructor UVU Email</label>
                  <Input
                    type="email"
                    placeholder="e.g. green.scholar@uvu.edu"
                    value={instructorEmail}
                    onChange={(e) => setInstructorEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New Instructor Display Name (Optional)</label>
                  <Input
                    placeholder="e.g. Professor Green"
                    value={instructorName}
                    onChange={(e) => setInstructorName(e.target.value)}
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">IA (Teaching Assistant)</label>
              <select
                className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={iaId}
                onChange={(e) => setIaId(e.target.value)}
              >
                <option value="none">None</option>
                <option value="custom">+ Add by email...</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} {u.display_name ? `(${u.display_name})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {iaId === "custom" && (
              <div className="border border-border bg-muted/30 rounded-md p-3 space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New IA UVU Email</label>
                  <Input
                    type="email"
                    placeholder="e.g. assistant.ta@uvu.edu"
                    value={iaEmail}
                    onChange={(e) => setIaEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New IA Display Name (Optional)</label>
                  <Input
                    placeholder="e.g. John TA"
                    value={iaName}
                    onChange={(e) => setIaName(e.target.value)}
                  />
                </div>
              </div>
            )}

            {formError && <p className="text-xs text-destructive font-medium">{formError}</p>}

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
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Course</DialogTitle>
            <DialogDescription>
              Update course details, active status, or assign instructors and IAs.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4 py-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Course Code</label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Course Title</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Term</label>
              <Input
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline justify-between gap-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Default Concepts
                </label>
                <span className="text-[10px] text-muted-foreground">
                  {concepts.length} selected
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Select default allowed structures for assignments in this course.
              </p>
              <DefaultConceptsPicker
                metadata={conceptMetadata}
                selected={concepts}
                onToggle={toggleConcept}
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Instructor</label>
              <select
                className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={instructorId}
                onChange={(e) => setInstructorId(e.target.value)}
              >
                <option value="none">None</option>
                <option value="custom">+ Add by email...</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} {u.display_name ? `(${u.display_name})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {instructorId === "custom" && (
              <div className="border border-border bg-muted/30 rounded-md p-3 space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New Instructor UVU Email</label>
                  <Input
                    type="email"
                    placeholder="e.g. green.scholar@uvu.edu"
                    value={instructorEmail}
                    onChange={(e) => setInstructorEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New Instructor Display Name (Optional)</label>
                  <Input
                    placeholder="e.g. Professor Green"
                    value={instructorName}
                    onChange={(e) => setInstructorName(e.target.value)}
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">IA (Teaching Assistant)</label>
              <select
                className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={iaId}
                onChange={(e) => setIaId(e.target.value)}
              >
                <option value="none">None</option>
                <option value="custom">+ Add by email...</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} {u.display_name ? `(${u.display_name})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {iaId === "custom" && (
              <div className="border border-border bg-muted/30 rounded-md p-3 space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New IA UVU Email</label>
                  <Input
                    type="email"
                    placeholder="e.g. assistant.ta@uvu.edu"
                    value={iaEmail}
                    onChange={(e) => setIaEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New IA Display Name (Optional)</label>
                  <Input
                    placeholder="e.g. John TA"
                    value={iaName}
                    onChange={(e) => setIaName(e.target.value)}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="edit-is-active"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded border-input text-primary focus:ring-primary"
              />
              <label htmlFor="edit-is-active" className="text-sm font-medium text-foreground cursor-pointer">
                Course is active
              </label>
            </div>

            {formError && <p className="text-xs text-destructive font-medium">{formError}</p>}

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
            <DialogDescription className="py-2 text-sm text-muted-foreground block">
              Are you sure you want to deactivate <span className="font-semibold text-foreground">&quot;{selectedCourse?.title}&quot; ({selectedCourse?.code})</span>?
              This will hide the course from normal staff and sandbox views, but historical records will be preserved.
            </DialogDescription>
          </DialogHeader>
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
