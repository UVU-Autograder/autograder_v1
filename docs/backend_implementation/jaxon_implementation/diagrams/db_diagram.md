Persistent M1 data model only. This diagram represents metadata stored in PostgreSQL and excludes student submissions, tracebacks, AI hint bodies, and other zero-retention pipeline artifacts.

```mermaid
classDiagram
    direction TB

    class User {
        +UUID id
        +String email
        +Boolean is_active
    }

    class Role {
        +UUID id
        +String name
    }

    class Course {
        +UUID id
        +String code
        +String name
        +String term
    }

    class Section {
        +UUID id
        +UUID course_id
        +String crn
        +String name
    }

    class StaffAccess {
        +UUID id
        +UUID user_id
        +UUID role_id
        +UUID course_id
        +UUID section_id
    }

    class Assignment {
        +UUID id
        +UUID course_id
        +String title
        +String canvas_id
        +DateTime due_date
        +Boolean sandbox_enabled
    }

    class AssignmentConfig {
        +UUID id
        +UUID assignment_id
        +JSON raw_config_json
        +DateTime updated_at
    }

    class ConceptSet {
        +UUID id
        +UUID course_id
        +String name
        +List allowed_concepts
    }

    class AssignmentConceptOverride {
        +UUID id
        +UUID assignment_id
        +List allowed_concepts
        +List restricted_concepts
    }

    class AssignmentArtifact {
        +UUID id
        +UUID assignment_id
        +String artifact_type
        +String storage_ref
        +String display_name
    }

    class TestCase {
        +UUID id
        +UUID assignment_id
        +String criterion_label
        +String student_visible_description
        +Int point_value
        +String pytest_artifact_ref
    }

    class RunSummary {
        +UUID id
        +UUID assignment_id
        +UUID actor_user_id
        +String workflow_type
        +String status
        +DateTime started_at
        +DateTime completed_at
        +Int total_submissions
        +Int success_count
        +Int warning_count
        +Int failure_count
        +Int timeout_count
        +JSON token_usage_metadata
        +String failure_summary
        +String moss_report_url
    }

    %% Relationships
    Role "1" --> "many" StaffAccess : assigned_in
    User "1" --> "many" StaffAccess : granted
    Course "1" *-- "many" Section : contains
    Course "1" --> "many" StaffAccess : scopes_visibility
    Section "0..1" --> "many" StaffAccess : scopes_edit_and_run_authority
    Course "1" *-- "many" Assignment : owns
    Course "1" *-- "many" ConceptSet : provides_defaults
    Assignment "1" *-- "1" AssignmentConfig : stores
    Assignment "1" *-- "0..1" AssignmentConceptOverride : overrides
    Assignment "1" *-- "many" AssignmentArtifact : stores
    Assignment "1" *-- "many" TestCase : grades_with
    Assignment "1" *-- "many" RunSummary : tracks_section_scoped_runs
    User "1" --> "many" RunSummary : initiates
```
