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
        default_concepts
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

    class AssignmentConfig {
        config_json
    }

    class AssignmentConcept {
        added_concepts
    }

    class AssignmentArtifact {
        artifact_key
        artifact_type
        storage_ref
    }

    class TestCase {
        config_test_key
        pytest_marker
        points
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
    Section "0..1" --> "many" StaffAccess : narrows_run_scope
    Course "1" *-- "many" Assignment : owns
    Assignment "1" *-- "1" AssignmentConfig : stores_app_owned_config
    Assignment "1" *-- "0..1" AssignmentConcept : stores_concept_additions
    Assignment "1" *-- "many" AssignmentArtifact : stores_file_body_refs
    Assignment "1" *-- "many" TestCase : exposes_derived_projection
    Assignment "1" *-- "many" RunSummary : tracks_workflows
    User "0..1" --> "many" RunSummary : initiates_staff_runs
```
