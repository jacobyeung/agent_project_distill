from pathlib import Path
p=Path('work/write_delivery.py');s=p.read_text();a=s.index("report=f'''");b=s.index("(O/'REPORT.md').write_text(report)",a)
s=s[:a]+'''report=f\'''Package `{token}` is resealed with an Orchard CPU check for both first items. **Local checks pass; submission requires the real Orchard CPU receipt.** No remote action or GPU run occurred.

The token stays unchanged because all 928 payload members and `0.tgz` remain byte-identical. Only operator files and their enclosing seals change. `OPERATOR_ONLY_AUDIT.json` records this comparison; `HASHES.json` records the final hashes.

| Implementation | File and line |
|---|---|
\'''+''.join(f'| {label} | `out/{name}:{line(O/name,needle)}` |\\n' for label,name,needle in refs)+f\'''
The allocated helper stages authenticated archives and restores the export before rehearsing `room_scene0155_00` and `r0_015bd4aaf6870d79bade`. It uses W5's allocation recipe: `general`, eight CPUs, 200G, `04:00:00`, and no GPU.

Both items run through real launch, mixed native mapping, frame SHA256 verification and PNG decoding, capped ParityGenerator, CallHook, the decode loop and official scoring. Weights, model forward, tokenizer, prompt tensors, audit enforcement and decode budget use explicit CPU stubs.

The helper embeds both finished records in `a/c/CPU.json` under `full_reader.records` and sets `full_reader_passed=true`. It also writes `FULL_READER.json`. Any failure aborts the check. The bootstrap requires both pass flags and matching payload, plan, input and operator hashes.

The first dev-S1 item has distinct native-answer and evaluation-ground-truth labels. The check records both official scores without changing either label. Stub scores establish execution, not model quality.

| Evidence | Result |
|---|---|
| `LOCAL_CPU_CHECK.json` | Both records finish on an initially empty local root with the real R0 tar and synthetic dev-S1 PNGs. |
| `LOCAL_NATIVE_CPU_CHECK.json` | The same check finishes with native `d1/scene0155_00` frame paths. |
| `CPU_HELPER_TEST.json` | The helper enforces stage/restore/rehearsal order and writes both records; failures publish no passing receipt. |
| `W5_BINDING_EQUIVALENCE.json` | All 36 dev-S1 room bindings match W5. |
| `OPERATOR_ONLY_AUDIT.json` | All 928 payload members remain identical; the same token is valid. |

The local fixture uses the production extractor and admitted `d` and `d/f` destinations. It reads the authenticated R0 tar in place. The synthetic dev-S1 fixture preserves the native `d1/<scene>` key and tests both native paths and the pinned metadata's content-addressed PNG paths. Synthetic digests exist only in fixture settings; no digest verifier is bypassed.

Local preparation stubs unavailable export weights, artifact construction and runtime versions. The helper orchestration test also stubs the allocation, namespace and storage proof. These tests validate the check implementation; the allocated Orchard run must validate the actual archives, restore and namespace.

The W5 comparison runs each source tree in an isolated interpreter. Native tasks, resolved anchor/dense paths, pinned SHA256 values, indices, slots, mapping digests, effective types, settings and finished journal types match for all 36 rows. W6 explicitly persists the effective type list; W5's settings and journals establish the same selection.

The plan still contains one development-only room read: 36 dev-S1 and 98 R0-dev items, tower, mode none, null_argmax, G3T memo on, no verification IDs, and no own-depth output. The item-set digest is `{plan['item_set_sha256']}`. No fitting ran.

The payload retains the reader, scorer, step-544 export, frame binding and input descriptors. `PATCH.diff` compares source and operator files against W5. `PAYLOAD_AUDIT.json` records the payload's W5 comparison separately from the operator-only reseal audit.

Latest suite results: **{passed} passed, {failed} failed**. `TESTS.txt` preserves the execution ledger; this table reports each suite's latest result. Unchanged reader/memo suites retain their passing evidence.

| Gate | Latest result | Tests | Log |
|---|---|---:|---|
\'''+ '\\n'.join(details)+f\'''

Production walltime remains `02:30:00`; the CPU check uses `04:00:00`. The read estimate is {price['read_seconds']:.1f} seconds. The return estimate is 10,428,800 bytes, below the 89.9 MB archive allowance and 100 MB pool cap. Production throughput, RSS and pool occupancy remain unmeasured.

`OPERATIONS_ROOM.md` gives exact placement, metadata-check, allocated CPU-check, pass-flag inspection, submit, fetch, unpack and scoring commands. It requires the passing Orchard receipt before submission.

All writes stayed inside W6. Tests used the supplied CPU Python with at most eight workers. No SSH, Git, network, submission, process kill or deletion ran. Rebuild the operator delivery with `out/build_operator.py` and `out/build_delivery.py`; verify it with `work/audit_operator_only.py` and `work/final_check.py`.

The report applies the no-archaeology and summary skills. The W5 comparison and reseal baseline remain because the requested equivalence and token checks require them.

| Artifact | Bytes | SHA256 |
|---|---:|---|
\'''+''.join(f"| `{n}` | {v['bytes']} | `{v['sha256']}` |\\n" for n,v in hashes.items())
''' +s[b:]
p.write_text(s)
