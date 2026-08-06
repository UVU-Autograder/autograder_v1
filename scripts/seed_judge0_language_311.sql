-- Idempotently seed custom Python 3.11.9 language entry in Judge0 database
INSERT INTO languages (id, name, compile_command, run_command, source_file, is_archived)
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
    compile_command = EXCLUDED.compile_command,
    run_command = EXCLUDED.run_command,
    source_file = EXCLUDED.source_file,
    is_archived = EXCLUDED.is_archived;
