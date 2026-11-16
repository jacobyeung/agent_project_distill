Cause: copied 0400 files and 0500 directories rejected ordinary writes; round-2 fails at b/r.sh on the observed Orchard fixture.
`tools/sealed_output.py:10` / `payload/d.py:57`: confine chmod/writes to the output; grant u+w to file and parent, restore exact modes in finally; refuse links/escapes.
`tools/make_deriver.py:126` generates `tools/derive_kit_h1.py` and `payload/d.py` with the same embedded writer.
`payload/d.py:454`: every replace_once patch uses it: b/r.sh (both patches), b/h.py, b/i.py, job.sh, b/c.sh and b/p0.sh.
`payload/d.py:481`: archive and 7.json copies, s1_record.json (:484), and archive.json (:499) preserve existing modes.
`payload/d.py:600`: initial b/ and job copies preserve source modes; k/o/runs creation (:602), k copies (:608) and add_k writes (:611) use scoped writes.
`payload/d.py:638`: config, 1.json, 0.json, launch.json (:672), SHA256SUMS.txt (:676) and ANON_OK.json (:678–680) preserve modes.
New k members inherit k/1.json's mode; renamed configs inherit the source config mode; new runtime dirs are 0700; source dirs retain exact modes.
`payload/d.py:682`: empty overrides preserve the root mode and add no absent runtime dirs; complete fixtures reproduce the entire source byte- and mode-identically.
`tools/orchard_records.py` / `payload/r.py:80,92`: temporary final launch and final certificate writes use the scoped writer; other writes target the mutable bundle only.
`payload/r.py:55,83,88`: empty reproduction and final comparison check modes explicitly and record mode digests; SHA256SUMS.txt itself remains byte-only.
Audit: `payload/z.sh:17–20` only checks sums/dispatches; `payload/v.py:27–54` only reads staging data and does not compare modes. Neither writes sealed members.
`tests/test_sealed_modes.py:64,69`: round-2 fails; H1, D0 and empty overrides pass on observed-mode and fully sealed fixtures, with source bytes/modes unchanged.
`tests/test_sealed_modes.py:87,112`: new files under 0500 dirs, restoration on failure, escape refusals, prepare, final comparison, mode-only rejection and certificate writes pass.
Two unavailable payloads use small stand-ins and a test-only manifest pin; complete production-kit availability remains unverified (`evidence/fix3_modes.json`).
PASS: four original checks, stop_bridge, fix1, visible_names, rv_mut, rv_g_a2, rv_gate and rv_g_fx (`evidence/fix3/tests.json`); CPU fallback reaches 200 and verifies its slot.
PASS: review syntax, unchanged RERUN_CHAIN.sh, deterministic repeated upload, archive metadata, embedded transport and payload sums (`evidence/fix3/package.json`). Existing chain_r1 was untouched.
`tools/audit_packet.py`, `tools/write_report.py` and `tools/seal_packet.py` regenerate DIFF.md, REPORT.md and SHA256SUMS.txt with current evidence; `tools/write_fix3.py` records full changed hashes.
Changed hashes: d.py 86b2444418f9275b, r.py cd30fd2dde869c51, sums af303c1927c0d9f2, orch_h1.sh 32868d37370d45eb (full values in evidence/hash_changes_fix3.json).
Upload SHA256: e3a462be5a09f4f69dc57441b1d046302d5cd646bf82b6f78285d8b50667c87c → 620e72ebf6c2727b920767d8fd9f4f5b092af513168c1f8bf2f7c89a52df5a9c; archive build/p_620e72ebf6c2727b.tar.
Identity 6e4f2846 and contract 9a527092 are unchanged, as are all IDs, trainer pins, fixture byte manifest and wrapper. The target-exists refusal remains active for operator re-upload.
Work stayed local and CPU-only; no SSH, network, Orchard, GPU, Git, deletion, chain creation or chain-runner modification occurred.
