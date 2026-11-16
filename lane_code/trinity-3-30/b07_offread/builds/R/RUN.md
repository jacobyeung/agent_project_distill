VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.

CPU validation and the four local rehearsals use fresh opaque RAM directories:

```bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
"$PY" -B -m pytest -p no:cacheprovider tests --basetemp=/dev/shm/b07_n4/a201 -q
"$PY" -B tests/rehearse.py vsi /dev/shm/b07_n4/a202
"$PY" -B tests/rehearse.py revsi /dev/shm/b07_n4/a203
"$PY" -B tests/rehearse.py vsi /dev/shm/b07_n4/a204 --done
"$PY" -B tests/rehearse.py revsi /dev/shm/b07_n4/a205 --done
```

The accepted-return tests reproduce all three budgets exactly, including B2048's 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4]. Fixture reports contain synthetic answers and cannot authorize submission.

Preparation requires the owner's final init-selection decision for a D0 export. Its selected hash and milestone must match the completion record, registered rule and D0-ended reference. Explicit `--export step544` omits init-selection. Choose one export per benchmark; the kit does not select a milestone.

```bash
"$PY" -B kit/rebind.py prepare --benchmark vsibench5130 --export "done:$SELECTED_DONE"   --init-selection "$INIT_SELECTION" --ledger /dev/shm/b07_n4/a206.jsonl   --mode production --token a0123456789abcdef --destination /dev/shm/b07_n4/a207
"$PY" -B kit/rebind.py submit-command --destination /dev/shm/b07_n4/a207   --ledger /dev/shm/b07_n4/a206.jsonl
```

Use `--benchmark revsi999t32` and a fresh token/destination for the other benchmark. `submit-command` only prints the operator command. It uses `a15_cot_ap` plus `secrets.token_hex(8)`, validates `^a15_cot_ap[0-9a-f]{16}$`, and requests `--export=NONE`, one GPU, 16 CPUs, 200 GB and six hours. A saved unambiguous `SUBMIT.out` is required by `record-submission`. Fetch and report retain the accepted identity checks and governed transport. No submission or transfer ran during this build.

Every batch has a compressed hex payload. Scans reject plain, hex and base64 forbidden spellings in the batch, nested member paths, environment and submission argv. Each forbidden logical component receives `x` plus 12 random hex digits, stable within the build. `out/NAME_MAP.json` and its SHA256 pin stay on Trinity. The packet contains a digest-to-token table; `xnames.py` resolves paths from that table and unchanged source bytes. Reader, scorer and item bytes remain identical. Named diagnostics receive random tokens. Packages are gzip-compressed tar files with external content pins.

The 288 video byte counts supplement the accepted hashes; staging verifies bytes and SHA256. Keep archive transfers serial and governed. See `OPEN_INPUTS.md` for live-runtime limits and `out/R3_VALIDATION.json` for CPU evidence.
