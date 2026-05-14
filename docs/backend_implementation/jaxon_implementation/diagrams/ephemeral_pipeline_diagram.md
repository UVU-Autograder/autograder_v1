Ephemeral grading pipeline model only. This diagram represents RAM-only or temp-workspace objects created during an active official batch or sandbox grading request and destroyed after completion or session exit. It also includes transient Judge0 submission/result artifacts and Kata-backed execution artifacts, which must be deleted or invalidated immediately after retrieval.

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

    class Judge0Submission {
        +String submission_token
        +Int language_id
        +Boolean delete_verified
    }

    class KataExecutionContext {
        +String vm_runtime
        +Boolean network_disabled
        +Boolean destroyed_after_run
    }

    class TestExecutionResult {
        +Int status_id
        +String status_description
        +Int passed_count
        +Int failed_count
        +Int earned_points
        +String compile_output
        +Int memory_kb
        +Int exit_code
        +String exit_signal
        +Float execution_time_s
        +Float wall_time_s
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
    SubmissionBundle "1" --> "0..1" Judge0Submission : submits_to
    Judge0Submission "1" --> "1" KataExecutionContext : executes_in
    Judge0Submission "1" --> "1" TestExecutionResult : returns
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
