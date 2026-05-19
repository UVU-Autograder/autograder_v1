Persistent M1 data model only. This diagram represents the product concepts stored in PostgreSQL and excludes student submissions, tracebacks, AI hint bodies, and other zero-retention pipeline artifacts.

```mermaid
classDiagram
    direction TB

    class User {
        email
        is_active
    }

    class Role {
        name
    }

    class Course {
        code
        name
        term
    }

    class Section {
        crn
        name
    }

    class StaffAccess {
        role_scope
        section_scope
    }

    class Assignment {
        title
        canvas_ref
        sandbox_enabled
    }

    class CourseEnrollment {
        email
        source
        is_active
    }

    class AssignmentConfig {
        config_json
    }

    class ConceptSet {
        allowed_concepts
    }

    class AssignmentConceptOverride {
        allowed_concepts
    }

    class AssignmentArtifact {
        artifact_type
        storage_ref
    }

    class TestCase {
        config_test_key
    }

    class RunSummary {
        workflow_type
        status
        total_submissions
        failure_summary
        token_usage_metadata
    }

    Role "1" --> "many" StaffAccess : assigned_in
    User "1" --> "many" StaffAccess : granted
    Course "1" *-- "many" Section : contains
    Course "1" --> "many" StaffAccess : scopes_staff_access
    Section "0..1" --> "many" StaffAccess : narrows_run_or_roster_scope
    Course "1" *-- "many" Assignment : owns
    Course "1" *-- "many" CourseEnrollment : authorizes_students
    Course "1" *-- "many" ConceptSet : provides_defaults
    Assignment "1" *-- "1" AssignmentConfig : stores_canonical_config
    Assignment "1" *-- "0..1" AssignmentConceptOverride : overrides_defaults
    Assignment "1" *-- "many" AssignmentArtifact : stores_assets
    Assignment "1" *-- "many" TestCase : exposes_derived_records
    Assignment "1" *-- "many" RunSummary : tracks_workflows
    User "1" --> "many" RunSummary : initiates
```
