# Edited source lines

Command: `python resume_audit.py`. Old/new intervals are inclusive; an empty interval denotes insertion/deletion.

## patches/tree_r1_to_f64.patch

- `tree_f64/student_pilot/b7_inputs.py`, old: none.
- `tree_f64/student_pilot/b7_inputs.py`, new: 44–48.
- `tree_f64/student_pilot/carrier_c1_data.py`, old: 164, 199, 216, 219, 231, 258, 629, 636, 646–647, 650.
- `tree_f64/student_pilot/carrier_c1_data.py`, new: 161, 165, 167–169, 203–210, 227, 230–231, 243–247, 274, 342–343, 647, 654, 663–664, 666–667, 670.
- `tree_f64/student_pilot/carrier_c1_run.py`, old: 635.
- `tree_f64/student_pilot/carrier_c1_run.py`, new: 635, 1062–1063, 1124, 1126, 1251–1252, 2124.
- `tree_f64/student_pilot/decoupled_v.py`, old: none.
- `tree_f64/student_pilot/decoupled_v.py`, new: 106–107.
- `tree_f64/student_pilot/frame_input.py`, old: none.
- `tree_f64/student_pilot/frame_input.py`, new: 1–91.
- `tree_f64/student_pilot/pose_samples.py`, old: 128.
- `tree_f64/student_pilot/pose_samples.py`, new: 128–130.
- `tree_f64/student_pilot/r1_handover.py`, old: 54–55.
- `tree_f64/student_pilot/r1_handover.py`, new: 26, 55–56, 118–120.
- `tree_f64/student_pilot/r1_training.py`, old: none.
- `tree_f64/student_pilot/r1_training.py`, new: 77–78.
- `tree_f64/tests/test_f64_layout.py`, old: none.
- `tree_f64/tests/test_f64_layout.py`, new: 1–276.

## read/reader_f64.patch

- `b/src/b/e2e_reader/parity.py`, old: 208.
- `b/src/b/e2e_reader/parity.py`, new: 83–88, 211–212, 216–222.
- `b/src/h1eval/h10/parity_adapter.py`, old: 134, 137, 218, 245.
- `b/src/h1eval/h10/parity_adapter.py`, new: 134, 137–138, 219–220, 247–248.
- `b/src/orchard_h10/prepare.py`, old: 62.
- `b/src/orchard_h10/prepare.py`, new: 62–63.

## Additional module

- `read/f64_read.py`: all lines are new.
- Exact removed/added text is recorded in `resume_review.json`; the independent tree comparison is `INDEPENDENT_TREE_DIFF.patch`.
