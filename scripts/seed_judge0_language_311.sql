-- Idempotently seed custom Python 3.11.9 language entry in Judge0 database.
-- Column names match Judge0 CE 1.13.1 schema (compile_cmd / run_cmd).
INSERT INTO languages (id, name, compile_cmd, run_cmd, source_file, is_archived)
VALUES (
    711,
    'Python (3.11.9)',
    NULL,
    '/usr/local/python-3.11.9/bin/python3.11 main.py',
    'main.py',
    false
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    compile_cmd = EXCLUDED.compile_cmd,
    run_cmd = EXCLUDED.run_cmd,
    source_file = EXCLUDED.source_file,
    is_archived = EXCLUDED.is_archived;
