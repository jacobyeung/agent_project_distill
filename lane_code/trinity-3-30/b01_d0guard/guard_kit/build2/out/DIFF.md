# Production changes against sealed C8r

The baseline is `../build/in_c8r_kit/code_c8r.tar`, SHA256 `f4535bc015da4a6e7f0d99e6db17a39fd49aa8d78dcf0a47d0aa5241b507f134`.
`DIFF_C8R.patch` and `DIFF.patch` contain the same complete unified diff against that archive, including newly bundled reviewed dependencies. The table lists every added or changed production block and its current line range. All inherited C8r members and the reviewed dependency bytes remain unchanged (`SOURCE_IDENTITY.json`).

The code inventory comes from `CODE_MANIFEST.json`; rehearsal scripts, tests, operator transfer helpers and backup files stay outside the production tar. The stage receipt fix changes `worker.py` and `transport.py`. Report commands use the operator-updated source pin and CONFIG artifact (`REPORT_PIN_G4.json`). ORCH accepted the seven sealed trainer-tree names at 1601Z; the naming projections do not alter trainer bytes.

| File | Current lines | Change | Reason / brief item |
|---|---|---|---|
| `out/guard_kit/admission.py` | 1–76 | insert | Native journal merge and request/score/geometry admission; G2 item 2, G3 item 1 |
| `out/guard_kit/checkpoint.py` | 1–78 | insert | Fresh checkpoint process, identity proof, published canary and native read; G1 items 3–5, G2 item 2 |
| `out/guard_kit/closure.py` | 1–158 | insert | Candidate config, source-seal, preparation and initialization-chain authentication; G2 item 1 |
| `out/guard_kit/fetch.py` | 1–15 | insert | Verify and unpack the plan-bound returned archive; G2 item 2 |
| `out/guard_kit/guard_backend.py` | 1–110 | insert | Re-derive export-dependent contracts while preserving C8r pins and restoration; G1 items 1–2 |
| `out/guard_kit/guard_core.py` | 1–154 | insert | Completion parsing, byte pins, ordered proof, canary and native rows; G1 items 1–5 |
| `out/guard_kit/guard_export.py` | 1–31 | insert | Bind candidate completion bytes and invoke unchanged reviewed export admission; G1 item 1 |
| `out/guard_kit/names.py` | 1–36 | insert | Neutral-name projection and byte-preserving round-trip audit; G1 item 6, G2 item 3 |
| `out/guard_kit/native_arm.py` | 1–38 | insert | Select only the native arm without editing kernel bytes or converting answers; G1 item 3 |
| `out/guard_kit/packet.py` | 1–199 | insert | Candidate plan and authority gates, pinned payload and command-line Slurm resources; G1 items 1,4,7, G2 item 2 |
| `out/guard_kit/pool.py` | 1–51 | insert | Reserve exclusive publication tokens and enforce result-pool bounds; G2 item 2 |
| `out/guard_kit/reviewed/chain_save.py` | 1–137 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/checker/common.py` | 1–43 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/checker/export_check.py` | 1–84 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/export_stage.py` | 1–224 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/orchard_job.py` | 1–279 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/orchard_results.py` | 1–194 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/orchard_stage.py` | 1–302 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/reviewed/return_io.py` | 1–68 | insert | Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1 |
| `out/guard_kit/stage_candidate.py` | 1–32 | insert | Run the reviewed full export checker inside the C8r namespace; G2 items 1–2 |
| `out/guard_kit/staging.py` | 1–92 | insert | Stage both exports, bind closure artifact bytes, reject hard links; G2 items 1–2 |
| `out/guard_kit/transport.py` | 1–147 | insert | Bound and authenticate publication, archive and returned stage evidence; G2 items 2,4, G4 fix 3 |
| `out/guard_kit/worker.py` | 1–145 | insert | Coordinate proof/candidate processes, retain stage receipts and bind report artifact/source; G2 item 2, G4 fixes 1,3 |
