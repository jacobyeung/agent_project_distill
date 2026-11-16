# EAT-1 report: eat1.adapters.gf1_tiny:make_reader

Artifact manifest /scratch/jjyeung/orch_n30/b03_e2etest/work/b5_gf1_tiny/artifact/ARTIFACT.json (sha256 a7c029a7acf811ae84ee08268df34d0ebddcc7e85b79d4b9c3df64b1d7c0a562); items 6; mode dynamic; started 2026-11-16T13:07:01Z.

| Clause | Status | Summary |
|---|---|---|
| A1 | PASS | 0 artifact, 2 code, 6 input, 0 outside-artifact data files opened after generate() started |
| A2 | FAIL | model entries per item {0: 6}; 0 tokens fed that neither the model chose nor a registered handler emitted; 0 static findings |
| A3 | PASS | 0 findings in 4 call-path files {} |
| A4 | FAIL | 2 offender groups (0 static) |
| A5 | PASS | parts {'iii': 'PASS', 'i': 'PASS', 'ii': 'PASS'} |

Overall: **FAIL**

## Per type (A6)

| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |
|---|---|---|---|---|---|
| direct | 2 | 0.000 | 0.00 | - | 0.001, 0.001, 0.001 |
| move | 2 | 0.000 | 0.00 | - | 0.009, 0.009, 0.016 |
| turn | 2 | 0.000 | 0.00 | - | 0.001, 0.001, 0.001 |

## Offenders by clause (file and line)

### A2

- model_entries x6 items ['direct_0', 'direct_1', 'move_0', 'move_1', 'turn_0', 'turn_1']  {}

### A4

- reader_error x6 items ['direct_0', 'direct_1', 'move_0', 'move_1', 'turn_0', 'turn_1']  {"detail": "ProgramRefusal: trace_program_version_missing"}
- answer_not_in_generated_sequence x6 items ['direct_0', 'direct_1', 'move_0', 'move_1', 'turn_0', 'turn_1']  {"answer": null}

