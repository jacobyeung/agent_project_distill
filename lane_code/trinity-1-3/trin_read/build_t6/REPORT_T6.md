# D0 milestone reader build_t6

Build_t6 provides strict uploader admission, scorer-compatible ITEMS export, optional model hard links, and a governed four-part GCS launcher. The full CPU suite passes: **260 tests**, including all 216 baseline cases and 44 new cases. `TESTS_T6_FULL_04.log` records the run with fresh basetemp `tests/t6_full_04` and the README command. System Python also accepts the new CLI help interfaces.

## Delivered contracts

- `stage-export --done` accepts the uploader's single plain-text line and the JSON form. Both require exactly object, positive integer bytes, and lowercase SHA256. The object must match `q8/8865619b/<run>_m<step>.tar` and the requested run/step. Invalid objects, extra fields/lines, duplicate JSON keys, bad hashes, and nonpositive sizes fail admission.
- `items --read OUT --step N --out ITEMS.jsonl [--a A]` imports the unchanged cont_ops `records()`/`write()` and `index()`/`align()` by path after checking their pinned SHA256. It requires complete main/away/forward membership, includes camera when present, and checks A544 metadata and membership. An explicit `--a` adds alignment against that input. `ITEMS.RECEIPT.json` records output SHA256, input hashes/sizes, scorer hashes, and family counts.
- `read --link-models` hard-links manifest-pinned staged base/export files into each family packet. It refuses different filesystems and archive models, checks hashes and inodes before and after execution, and removes model bytes from the reserve while retaining the 200 GiB floor. Default reads still copy models. CARD, model identity receipts, MODELS_LINKED, EXIT, and SANDBOX carry the relevant evidence.
- `launch_gcs.py LANE DONE_FILE OUT` retains the launch_pull2 gate and governor arguments. Bash stops itself before gcloud starts; ratelimit is a registered member; bash never execs away. Four ordered parts stream under `timeout 14400`. The launcher waits, hashes the partial file, renames the stream record to `.done.<epoch>`, writes the receipt, and publishes only a byte/hash match. It never retries.

## Packet and sandbox evidence

The active journal path is `<OUT>/<family>/direct/<family>/results/budget_2048/0/items_a0.jsonl`. The accepted direct packet uses `direct/<family>` where the Orchard kit uses its outer `a0` directory; both retain the B2048 arm and `a0` attempt. The worker authenticates this journal and `report/B2048.json` in COMPLETE. The milestone summary also pins the report. The exporter uses these exact paths and refuses changed inputs.

Each linked packet is dry-bound on CPU before its models are prepared. The original kit then reuses the authenticated model identity receipts. `SANDBOX.json.namespace_argv` includes `--ro-bind <packet>/direct/<family>/models <packet>/direct/<family>/models` after writable root binds. It also includes read-only binds for physical and logical source directories. `MODELS_LINKED.json.bwrap_args` records the exact arguments. The full export checker remains in the generation path.

The CPU tests confirm inode equality, unchanged-kit receipt reuse without copies, simulated cross-filesystem refusal, and failure after a same-size byte mutation. Launch integration checks CARD/EXIT evidence and the exact sandbox arguments. Fresh-process tests reuse the CPU binding for all four families and reject a changed binding pin.

Scorer tests extend the inherited miniature packet journal with accepted A544 IDs/metadata and the pinned e193 inventory. They exercise all 1,825 core records and optional 450 camera records, plus report/journal corruption, membership, step, metadata, completion, and scorer-source pin refusals. These are synthetic execution records; they do not establish new model accuracy.

The fake GCS tests execute real CPU subprocesses. Fake registration verifies that the reader is stopped bash and that the member, expected bytes, and PRIO arguments match before sending SIGCONT. Fake gcloud verifies all four URLs and their order. Tests cover successful publication, wrong size, same-size wrong hash, failed streams, retained partial files, and refusal to retry. No real registration or network request occurs.

## Limits and retained files

No real GCS transfer, production staging, namespace model run, GPU execution, full production-weight scan, or D0 score was performed. Production remains subject to the README's staging, frame, proof, orchestrator, and heavy-I/O prerequisites. Read-only namespace mounts protect generation; host processes can still modify shared hard-link bytes, which the post-run audit detects.

Only build_t6 was edited. No SSH, network, Git, GPU, or deletion command ran. Cont_ops, root, dl, kit_src, build, and build_t5 sources were read-only. `INPUT_PINS_T6.json` identifies the relevant source and module bytes. `DIFF.md` classifies each change as PATH/ENV or BEYOND.

An unreferenced `compact_items.py` and nested `build_t5/` directory were found in the target and preserved without modification. The CLI and installed bundle use `items_export.py`; neither additional artifact participates in execution or test collection. Retained test evidence is also excluded from collection, so its intentional cyclic links cannot be followed by pytest.

The README and report apply the no-archaeology skill. The explicitly requested baseline comparison in DIFF is the only retained historical framing.
