import CourseCard from "@/components/ui/coursecard";

export default async function DashboardPage() {
  let courses: any[] = [];
  let isBackendOffline = false;

  try {
    const response = await fetch("http://127.0.0", {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });

    const data = await response.json();

    if (data && Array.isArray(data.courses)) {
      courses = data.courses;
    } else if (Array.isArray(data)) {
      courses = data;
    }
  } catch (error) {
    console.error(error);
    isBackendOffline = true;

    // IMPORTANT: assign to outer variable (no "const")
    courses = [
      {
        id: "cs1400",
        title: "Introduction to Python (Local Mock)",
        term: "Fall 2026",
      },

        {
        id: "cs1410",
        title: "Data Structure and Algorithms (Local Mock)",
        term: "Fall 2026",
      },
    ];
  }

  return (
    <div className="p-8">

      {/* 🔴 Backend warning message */}
      {isBackendOffline && (
        <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded">
          ⚠ Backend connection failed — showing fallback data
        </div>
      )}

      {/* 📦 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {courses.map((course) => (
          <CourseCard key={course.id} course={course} />
        ))}
      </div>

    </div>
  );
}