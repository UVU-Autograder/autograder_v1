Ephemeral grading pipeline model only. This diagram represents the workflow stages that exist only during an active official batch or sandbox grading request and are destroyed after completion or session exit.

```mermaid
flowchart TD
    A[Intake request] --> B[Validate auth, assignment context, and upload shape]
    B --> C[Create ephemeral workspace]
    C --> D[Prepare submission bundles]
    D --> E[Run constraint checks]
    E --> F[Execute tests in isolated runtime]
    F --> G[Shape grounded grading results]
    G --> H[Generate explanation text]
    H --> I{Workflow type}
    I -->|Official| J[Package staff-facing export artifacts]
    I -->|Sandbox| K[Return on-screen feedback]
    J --> L[Cleanup boundary]
    K --> L
    L --> M[Destroy workspace and transient artifacts]
```

## Diagram Notes

- Persistent inputs such as assignment config, assignment artifacts, derived test metadata, and staff access checks inform the workflow but are not recreated as persistent outputs.
- Cleanup is mandatory for both official and sandbox workflows.
- The diagram is intentionally technology-neutral; concrete execution, AI, queue, and storage choices live in the prose specs.
- Official-run review is preview-only in M1; this diagram focuses on the ephemeral grading and cleanup lifecycle.
