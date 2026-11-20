Compared 344 files: 326 IDENTICAL and 18 DIFFERS; hashes are in LOOP_HASHES.md and LOOP_HASHES.json.
The 319 tree files plus the eight requested kit files contain 320 IDENTICAL and 7 DIFFERS; helper traversal adds 17 rows.
Run4 passed 8/9 rows; “milestone export / local receipt / kit copier” was NOT PROVED.
Run5 covered that local copier row via rehearsal5/target/o/rehearsal/live/gcs_m2.done; its budget phase refused.
The copier files are not all byte-identical: pc.py and sr.py match launch; pc.sh adds a launch-only ep.py call in tk_live_finish.
Run5 imported pc.py with local stand-ins; it did not exercise the pc.sh shutdown path or prove production transport.
Differing tree files: tree/launch_r1/entry.py, tree/launch_r1/production_proof.py, tree/student_pilot/r1_handover.py, tree/student_pilot/r1_launch22.py.
Differing kit files: kit/b/a.py, kit/b/cs.py, kit/b/ep.py, kit/b/i.py, kit/b/pc.py, kit/b/pc.sh, kit/b/pl.py.
Differing kit files: kit/b/px.py, kit/b/rb.py, kit/b/rg.py, kit/b/rv.py, kit/b/sc.py, kit/b/sv.py, kit/b/z.py.
PROVENANCE.md identifies recorded paths/seals and authenticates recovered kit bytes; DERIVATION.md explains the closure; DIFFS/ has every diff.
