import { useState, useEffect } from "react";
import Link from "next/link";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
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
import { CourseSectionsDialog } from "./course-sections-dialog";
import { CourseForm, CourseFormUser } from "./course-form";

type UserSummary = CourseFormUser;

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
  const [isSectionsOpen, setIsSectionsOpen] = useState(false);

  // Selected course for Edit / Delete / Sections
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
    setConcepts([...(course.default_concepts ?? [])]);
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

  const openSectionsDialog = (course: CourseAdminDetail) => {
    setSelectedCourse(course);
    setIsSectionsOpen(true);
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
        ia_email?: string | null;
        ia_name?: string | null;
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
        const found = users.find((u) => String(u.id) === instructorId);
        if (found) {
          payload.instructor_email = found.email;
        }
      }

      if (iaId === "custom" && iaEmail.trim()) {
        payload.ia_email = iaEmail.trim().toLowerCase();
        payload.ia_name = iaName.trim() || null;
      } else if (iaId !== "none" && iaId !== "custom") {
        const found = users.find((u) => String(u.id) === iaId);
        if (found) {
          payload.ia_email = found.email;
        }
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
                  <Button variant="outline" size="sm" onClick={() => openSectionsDialog(course)}>
                    Sections
                  </Button>
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
          <CourseForm
            code={code}
            setCode={setCode}
            title={title}
            setTitle={setTitle}
            term={term}
            setTerm={setTerm}
            concepts={concepts}
            toggleConcept={toggleConcept}
            conceptMetadata={conceptMetadata}
            users={users}
            instructorId={instructorId}
            setInstructorId={setInstructorId}
            instructorEmail={instructorEmail}
            setInstructorEmail={setInstructorEmail}
            instructorName={instructorName}
            setInstructorName={setInstructorName}
            iaId={iaId}
            setIaId={setIaId}
            iaEmail={iaEmail}
            setIaEmail={setIaEmail}
            iaName={iaName}
            setIaName={setIaName}
            formError={formError}
            isSubmitting={isSubmitting}
            submitLabel="Create Course"
            submittingLabel="Creating..."
            onSubmit={handleAddSubmit}
            onCancel={() => setIsAddOpen(false)}
            codePlaceholder="e.g., cs1400"
            titlePlaceholder="e.g., Fundamentals of Programming"
            termPlaceholder="e.g., Fall 2026"
          />
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
          <CourseForm
            code={code}
            setCode={setCode}
            title={title}
            setTitle={setTitle}
            term={term}
            setTerm={setTerm}
            concepts={concepts}
            toggleConcept={toggleConcept}
            conceptMetadata={conceptMetadata}
            users={users}
            instructorId={instructorId}
            setInstructorId={setInstructorId}
            instructorEmail={instructorEmail}
            setInstructorEmail={setInstructorEmail}
            instructorName={instructorName}
            setInstructorName={setInstructorName}
            iaId={iaId}
            setIaId={setIaId}
            iaEmail={iaEmail}
            setIaEmail={setIaEmail}
            iaName={iaName}
            setIaName={setIaName}
            showActiveToggle={true}
            isActive={isActive}
            setIsActive={setIsActive}
            formError={formError}
            isSubmitting={isSubmitting}
            submitLabel="Save Changes"
            submittingLabel="Saving..."
            onSubmit={handleEditSubmit}
            onCancel={() => setIsEditOpen(false)}
          />
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

      {/* --- COURSE SECTIONS DIALOG --- */}
      <CourseSectionsDialog
        isOpen={isSectionsOpen}
        onOpenChange={setIsSectionsOpen}
        course={selectedCourse}
      />
    </div>
  );
}
