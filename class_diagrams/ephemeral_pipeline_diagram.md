Ephemeral grading pipeline model only. This diagram represents RAM-only or temp-workspace objects created during an active official batch or sandbox grading request and destroyed after completion or session exit.

```mermaid
classDiagram
    direction TB

    class EphemeralWorkspace {
        +UUID workspace_id
        +String workflow_type
        +String temp_path
        +DateTime created_at
        +DateTime destroyed_at
    }

    class SubmissionBundle {
        +String submission_id
        +String source_type
        +String canvas_identifier
    }

    class StudentCode {
        +String filename
        +Bytes source_bytes
        +String extracted_path
    }

    class ConstraintCheckResult {
        +String status
        +List warnings
        +List hard_blocks
        +Boolean blocks_execution
    }

    class TestExecutionResult {
        +String status
        +Int passed_count
        +Int failed_count
        +Int earned_points
        +Float execution_time_s
    }

    class TracebackBundle {
        +List tracebacks
        +List failing_tests
    }

    class AIHintRequest {
        +String assignment_context
        +List allowed_concepts
        +String test_summary
    }

    class AIHintResponse {
        +String feedback_text
        +Int prompt_tokens
        +Int completion_tokens
    }

    class FeedbackDraft {
        +Int projected_score
        +List warnings
        +String rendered_feedback
        +String html_output
    }

    class ExportBundle {
        +String csv_path
        +String html_zip_path
        +String moss_report_url
    }

    class Assignment {
        <<persistent input>>
    }

    class AssignmentConfig {
        <<persistent input>>
    }

    class AssignmentArtifact {
        <<persistent input>>
        +String storage_ref
    }

    class TestCase {
        <<persistent input>>
    }

    EphemeralWorkspace "1" *-- "many" SubmissionBundle : contains
    SubmissionBundle "1" *-- "many" StudentCode : extracts
    SubmissionBundle "1" --> "1" ConstraintCheckResult : checked_by
    ConstraintCheckResult "1" --> "1" SubmissionBundle : gates_execution
    SubmissionBundle "1" --> "1" TestExecutionResult : executed_as
    TestExecutionResult "1" --> "0..1" TracebackBundle : emits
    SubmissionBundle "1" --> "0..1" AIHintRequest : builds
    AIHintRequest "1" --> "0..1" AIHintResponse : receives
    SubmissionBundle "1" --> "1" FeedbackDraft : assembles
    AIHintResponse "0..1" --> "1" FeedbackDraft : enriches
    TestExecutionResult "1" --> "1" FeedbackDraft : grounds
    EphemeralWorkspace "1" --> "0..1" ExportBundle : packages_official_results

    Assignment "1" --> "many" SubmissionBundle : scopes
    AssignmentConfig "1" --> "many" AIHintRequest : informs
    AssignmentArtifact "1" --> "many" SubmissionBundle : supports
    TestCase "1" --> "many" TestExecutionResult : defines
```
