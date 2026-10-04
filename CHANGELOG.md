# Changelog

## 0.1.0a1

First public alpha candidate.

- One local SQLite file, root table and SQL condition produce a branch with required FK parents.
- Preserve ordinary tables, indexes, views, triggers, defaults, generated columns, rowids, sequences and application/user versions.
- Read-only source snapshot, row/time limits, foreign-key/integrity checks and publication without replacing an existing destination.
- Standard-library Python API and JSON CLI, including JSON errors for invalid arguments.
- Match foreign keys with the parent's collation and affinity, including TEXT parents referenced by NUMERIC children.
- Authored task-board example and an interactive visual explanation with downloadable results.

This alpha does not mask data or automatically minimize failing examples. External adoption and net time savings have not been demonstrated.
