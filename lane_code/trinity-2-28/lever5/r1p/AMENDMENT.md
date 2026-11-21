# Rank 1 gate amendment (ORCH RULING 2026-11-21T18:48Z), registered before any cell a-g or BOX value was read

Reason: the registered parity gate compares the dump with T1's served cameras, bounded by twice T1's own repeat deviation.
G3T's output depends on the process's prior call history (HISTORY_DIAG.txt): the dump's first capture equals T1 bit for bit, the 59
later captures differ, and T1's own later repeats of its first capture differ from its first pass by 0.00186 m. The dump is
bit-identical across three runs on two nodes. The gate therefore cannot be met by a dump whose call history differs from T1's job.

Amended gate (replaces the two STOP gates of relift.py; nothing else changes):
(i) every depth-free gap check matches (unchanged; a mismatch still raises);
(ii) cell (a) is relifted from the same dump, the same 150-item set, and the same code path as cells b-g, so every comparison is paired
    inside one dump;
(iii) camera/scale parity against T1 (per dataset: captures and items within T1's bound, max deviation per field) and the printed-gap
    parity of a(dump) against T1 (per dataset: items at 0.00 m, at 0.01 m, beyond) are reported and do not gate.
The BOX dev check (vote_10_3_best against the served rule) reads the same dump under the same amendment. Its code is unchanged;
it executes the amended relift prefix.

Implementation (lane copies; originals untouched):
- /scratch/jjyeung/orch_n30/lever5/r1p/r1/relift.py = lever1_c/r1/relift.py with: the docstring extended; the camera-parity STOP replaced
  by result['camera_parity_vs_t1']=camera_report(depths); the printed-gap STOP replaced by parity.gating=False plus
  parity.by_dataset=gap_report(...) (buckets 0.00, 0.01, beyond, missing); result['gate'] records the amendment; three new report-only functions (_ds, camera_report, gap_report). Diff: r1p/relift.diff.
- /scratch/jjyeung/orch_n30/lever5/r1p/boxdev/run.py = lever1_c/boxdev/run.py byte-identical; SOURCE_PINS.json repoints relift.py and
  depth_format.py to the lane copies. Note: lever1_c/boxdev's original pin for depth_format.py (18405332...) predates the r1 kit's
  reseal; the r1 kit's SHA256SUMS seals depth_format.py at 2c7db4f3..., which is the version the dump was written and read with, so the
  lane pin uses 2c7db4f3.
- Inputs: dump lever1_c/r1/returned/0.gz (job 174135; receipt 4.json), bit-identical to 174200 and 174208.

Integrity fix found at first run (before any cell was computed; the run raised and wrote nothing): the original population check
`{join keys} != {funnel object keys}` fails on vsi590k_045785, whose JOIN_T1 row is item-level ("stage U, no recorded object call") while
FUNNEL_T1 holds its two object keys. The original code never reached this line (it stopped at the parity STOP). The lane copy now
requires: every object-level join key is a funnel key; the funnel keys missing from the join are exactly the objects of the item-level
join rows; every item-level join row has stage U. Diff in relift.diff.
Review: REVIEW_AMENDMENT.md GO (F1 explicit inputs applied; F2/F3 text fixed); REVIEW_FIX.md NO-GO pending one line, applied verbatim (fk-jk equals the item-level items' funnel objects).
