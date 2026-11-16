# Source changes

The exact source patch is `DIFF.patch`. Each changed block appears below. All inherited C8r files and reviewed stager files remain byte-identical (`SOURCE_IDENTITY.json`). Naming projections are not integrated into the runtime.

The admission-specific patch against the sealed G2 source is `G3_ADMISSION.patch`. Canonical JSON treats tuples and lists with the same contents equally, while preserving differences such as boolean versus integer values. The existing non-answer score-zeroing policy still applies before comparison. Key cardinality, membership, full-denominator, parity, request binding, score and geometry checks remain enforced. The accepted rows come from the JSON journal.

`out/tests/test_g2.py` exercises tuple/list admission, a changed-score refusal with `MERGE_DIFF.json`, missing/foreign/duplicate keys, absent-versus-null diagnostics, boolean/integer differences and downstream parity/denominator checks (`G2_TESTS.json`).

`work/family.py`, `work/seal.py --g3` and `work/finish.py --g3` refresh and verify the original production member inventory. `G3_SEAL.json` verifies that only `admission.py` differs inside the code tar. Rehearsal files and `.g2_orig.py` backups remain excluded. The operator's mount splitting, torchvision overlay and positional-argument forwarding remain rehearsal-only (`rehearsal/RUNBOOK.md`).

| File | Current lines | Change | Reason / brief item |
|---|---|---|---|
| `out/guard_kit/admission.py` | 1–76 | insert | Native-only journal merge, request/score/geometry admission; item 2 |
| `out/guard_kit/admission.py` | 14–27 | canonical JSON comparison | Compare per-key digests after the existing non-answer score normalization; refuse differing content and continue with journal rows; G3 item 1 |
| `out/guard_kit/admission.py` | 18–26 | mismatch diagnostics | Write differing keys and fields to `MERGE_DIFF.json`; distinguish an absent field from JSON null; G3 item 1 |
| `out/guard_kit/checkpoint.py` | 1–78 | insert | Fresh checkpoint process, proof, published canary and native read; item 2,4 |
| `out/guard_kit/closure.py` | 1–158 | insert | Candidate closure identity, source seals and hash chain; item 1 |
| `out/guard_kit/fetch.py` | 1–15 | insert | Verify and safely unpack a plan-bound return; item 2 |
| `out/guard_kit/guard_backend.py` | 9–9 | insert | Select the staged logical source root in checkpoint children; item 2 |
| `out/guard_kit/guard_backend.py` | 15–15 | replace | Select the staged logical source root in checkpoint children; item 2 |
| `out/guard_kit/packet.py` | 1–1 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 3–4 | insert | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 6–8 | insert | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 12–12 | insert | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 15–19 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 22–22 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 24–24 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 26–26 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 28–28 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 30–30 | insert | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 32–64 | insert | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 73–79 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 81–87 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 89–122 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 126–187 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/packet.py` | 193–193 | replace | Exact authority gates, bounded payload and command-line resources; item 2 |
| `out/guard_kit/pool.py` | 1–51 | insert | Exclusive token and inherited result-pool bound; item 2 |
| `out/guard_kit/stage_candidate.py` | 1–32 | insert | Call unchanged reviewed staging with the C8r checker namespace; item 1,2 |
| `out/guard_kit/staging.py` | 1–92 | insert | Dual export staging, closure mounting, hard-link rejection; item 1,2 |
| `out/guard_kit/transport.py` | 1–127 | insert | Bound archives, verify local/cloud copies and returned admission; item 2,4 |
| `out/guard_kit/worker.py` | 1–113 | insert | Coordinate fresh processes, durable early receipts and final publication; item 2 |
