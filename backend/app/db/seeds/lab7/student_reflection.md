# Lab 7 Reflection Responses

1. Why do we use `default_factory` when initializing a list field in a data class?
   - `default_factory=list` ensures that a new empty list instance is instantiated for each new object rather than sharing a single mutable default list across all instances.

2. What could go wrong if multiple students shared the same default list?
   - Modifying the course list for one student would inadvertently mutate the course list for every student sharing that default list.

3. How does putting methods like `enroll` and `total_courses` inside the class help with code organization?
   - It encapsulates student-related behavior directly alongside student state data, improving cohesion and maintainability.
