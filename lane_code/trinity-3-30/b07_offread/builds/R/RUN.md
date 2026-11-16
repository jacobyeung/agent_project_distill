VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.

CPU validation and the four local rehearsals use fresh opaque RAM directories:

```bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
RUN_ID=$("$PY" -B -c 'import secrets; print(secrets.token_hex(6))')
export ROFF2_ROOT=/tmp/a_900000_$RUN_ID
"$PY" -B -m pytest -p no:cacheprovider tests --basetemp=/dev/shm/b07_n7/a${RUN_ID}_201 -q
"$PY" -B tests/rehearse.py vsi /dev/shm/b07_n7/a${RUN_ID}_202
"$PY" -B tests/rehearse.py revsi /dev/shm/b07_n7/a${RUN_ID}_203
"$PY" -B tests/rehearse.py vsi /dev/shm/b07_n7/a${RUN_ID}_204 --done
"$PY" -B tests/rehearse.py revsi /dev/shm/b07_n7/a${RUN_ID}_205 --done
```

The accepted-return tests reproduce all three budgets exactly, including B2048's 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4]. Fixture reports contain synthetic answers and cannot authorize submission.

Preparation requires the owner's final init-selection decision for a D0 export. Its selected hash and milestone must match the completion record, registered rule and D0-ended reference. Explicit `--export step544` omits init-selection. Choose one export per benchmark; the kit does not select a milestone.

```bash
"$PY" -B kit/rebind.py prepare --benchmark vsibench5130 --export "done:$SELECTED_DONE"   --init-selection "$INIT_SELECTION" --ledger /dev/shm/b07_n7/a${RUN_ID}_206.jsonl   --mode production --token a0123456789abcdef --destination /dev/shm/b07_n7/a${RUN_ID}_207
"$PY" -B kit/rebind.py submit-command --destination /dev/shm/b07_n7/a${RUN_ID}_207   --ledger /dev/shm/b07_n7/a${RUN_ID}_206.jsonl
```

Use `--benchmark revsi999t32` and a fresh token/destination for the other benchmark. `submit-command` only prints the operator command. It uses `a15_cot_ap` plus `secrets.token_hex(8)`, validates `^a15_cot_ap[0-9a-f]{16}$`, and requests `--export=NONE`, one GPU, 16 CPUs, 200 GB and six hours. A saved unambiguous `SUBMIT.out` is required by `record-submission`. Fetch and report retain the accepted identity checks and governed transport. No submission or transfer ran during this build.

Every batch has a compressed hex payload. Scans reject plain, hex and base64 forbidden spellings in the batch, nested member paths, environment and submission argv. Each forbidden logical component receives `x` plus 12 random hex digits, stable within the build. `out/NAME_MAP.json` and its SHA256 pin stay on Trinity. The packet contains a salted digest-to-token table; `xnames.py` resolves paths from that table and unchanged source bytes. Reader, scorer and item bytes remain identical. Named diagnostics receive random tokens. Packages are gzip-compressed tar files with external content pins.

The 288 video byte counts supplement the accepted hashes; staging verifies bytes and SHA256. Keep archive transfers serial and governed. See `OPEN_INPUTS.md` for live-runtime limits and `out/R5_VALIDATION.json` for CPU evidence.

The shell launcher embeds the same opaque AP interpreter path that the namespace binds. Media lookup uses SHA-keyed local paths and a private runtime alias table. Both bwrap and subprocess arguments pass the forbidden-word scan after mapping. Native child logs pass through a reusable filtered pipe and remain in the job's log files.

Run the production-root CPU rehearsal from build N with `"$PY" -B validate_n7.py r_prod <fresh-label>`. It runs the namespace builder and checks the shell target against its bind. Production still requires a live transport-only rehearsal.

Each packet carries a 32-byte public salt. The builder computes HMAC-SHA256 with the Trinity-only secret over SHA256 of canonical JSON member pins: sorted physical member paths mapped to SHA256 content hashes, excluding `x0.json`, with compact JSON separators. The secret file contains 64 hex characters, which the builder decodes before HMAC. Tokens and aliases use SHA256(salt bytes + UTF-8 logical name). Build-side maps keep their unsalted keys; the runtime reads the salt before learning or resolving names and rejects a table without it. Packaging refuses a missing secret. Tests inject a synthetic secret through `A0_BUILD_SECRET_FILE`; production uses the protected Trinity secret. The secret never enters a packet or report.

The unsalted dictionary gate must find zero keys for every WORDS entry and NAME_MAP name. A public salt still permits dictionary guesses that include that salt; this format does not promise dictionary resistance. In-job file contents are exempt from the naming rule. File paths, child arguments, environment and job names retain their naming checks.

The production-root gate runs from build R: `"$PY" -B -m pytest -p no:cacheprovider tests/test_review_offnative2.py tests/test_prodroot.py --basetemp=/dev/shm/b07_n7/gate_$RUN_ID -q`. Keep the `ROFF2_ROOT` export above. F1/F2 and all three mapping-aware production-root cases must pass; F3 runs in N.
