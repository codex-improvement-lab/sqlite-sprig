# Validation

This is an alpha, developed and tested locally on Windows with Python 3.12 and SQLite 3.53. Hosted Linux/macOS/Windows checks are defined in CI; their result must be read from the current commit's run. Hosted macOS is not a physical-device acceptance test.

The behavior suite covers branch scope, parent cycles, composite and implicit parent keys, `WITHOUT ROWID`, NOCASE matching, parent TEXT versus child NUMERIC affinity, unique-column foreign keys, NULL references, generated columns, rowids/BLOBs/quoted identifiers, sequences and version pragmas, parent-only selection, row/time limits, invalid references, virtual-table refusal and an output-publication race. CLI checks exercise JSON errors and refusal to overwrite a finished result. Clean-wheel validation installs outside the checkout and checks actual view/default/trigger behavior.

The included task board is authored data. Its three branches produce 11, 9 and 8 rows from 24, depending on the selected card. These figures describe selected rows, not compression or execution savings.

Before this release, a frozen prototype was offered to one of two independent internal agents on an authored task. Both arms had prepared environments and could use direct Python sqlite3, Subsetter 0.4.4 or Pinkmask 1.5.0. The baseline chose a custom sqlite3 script; the product arm chose the prototype and wrote independent validation. Both produced the correct 11-row database. A parent verifier checked the frozen source/prototype hashes, exact rows/schema, foreign keys, view, subsequent writes and unchanged output bytes.

Self-reported intervals were 107.327 and 100.304 seconds. Installation costs were excluded. There was one task and one agent per arm, no repeated sampling, and no population-level inference. Both authored a helper script and performed inspection. We make no measured speedup claim.

The frozen prototype's ordinary JOIN was later found to mishandle a parent TEXT/child NUMERIC affinity case. This release strips the child's expression affinity and adds a bidirectional regression. The original comparison artifact remains frozen; its integer-key task was not affected. Relevant SQLite semantics: [foreign-key comparison](https://www.sqlite.org/foreignkeys.html) and [expression affinity](https://www.sqlite.org/datatype3.html).

External independent use, repeat adoption, large-database performance and full application compatibility have not been established.
