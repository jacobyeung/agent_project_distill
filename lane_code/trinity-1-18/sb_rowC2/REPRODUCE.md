The packet remains unadmitted until N accepts tally traces. Run these commands from this workspace with the named input paths present:

```sh
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
cc -O2 -shared -fPIC edit_filter.c -o edit_filter.so
/scratch/jjyeung/envs/p1cpu/bin/python -B build_rows.py
/scratch/jjyeung/envs/p1cpu/bin/python -B check_rows.py
```

`CHECKS.json` records semantic checks and unchanged native intake results separately. Inspect `required_all_checks_pass`; a successful checker process does not mean the native grammar accepted the rows. A build cell shortage or incorrect GT assertion stops the process.

The generator pins the local v7 database, removal list, room authorities, wording references, and w19 code. It groups structured B12 instance IDs by their first-seen frame, rejects conflicting category records, and selects each unordered category pair once per identical clip. It retains exact source rows in `SOURCE_ROWS.jsonl` for review. The standalone `tally_gate.py` is an additional semantic check, not a replacement for N's validator.

After reviewing all thirty examples, bind the review to the current `READ30.md` hash in `MANUAL_REVIEW.json`, then run:

```sh
/scratch/jjyeung/envs/p1cpu/bin/python -B package_rows.py
```

The package includes editable source code, rows, source records, checks, the full sample, and the report. Its companion `.sha256` file binds the tar archive. Image bytes, rasters, the complete source database, and the external kit are referenced by their recorded pins rather than included.
