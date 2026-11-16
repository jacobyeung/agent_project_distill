# K1 lost files: hash check, readers, generators, pins (lane k1_rules, trinity-1-18, 2026-11-15)

## (a) K1_RULES.json hash
- `kit_k1a/work/preregister.py:8` writes `json.dumps(k1_report.RULES, indent=2)+"\n"`; `RULES` is the literal at `kit_k1a/work/k1_report.py:8-14` (sha 607a8a16..., pinned in `kit_k1a/out/DEPENDENCIES.json:96` and `k1_ops/work/T1_SHA256SUMS:110`).
- Check 1: system python, `ast` evaluation of the literal (no import): sha256 cb0aadee89c86e3db41c33d450eee6d7f58558d63f56d3d189e744277ad23269, 815 bytes.
- Check 2: kit interpreter `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, real `import k1_report` (vendor path shimmed to `kit_k1a/native_kit/vendor_sam/vendor`, no bytecode written): same sha, same 815 bytes; the lane file equals `RULES` byte for byte.
- Registered value: `distill_design/REFREEZE_PREREGISTRATION_20261115.json` line 10 (`/inputs`) and line 55 (`/k1_rules_relation/sha256`); the `.md` twin line 67 gives the prefix `cb0aadee…`. Match.
- Lane copy: `work/K1_RULES.json`, `work/K1_RULES.sha256` (preregister.py's format). Nothing written into the kit.

## (b) RUNCARD_K1.md and PROOFS.md
- Readers: only `kit_k1a/work/audit_delivery.py:6-7`, which asserts each file exists (`is_file`) and reads no content. No code in `kit_k1a` or `k1_ops` hashes or parses either file.
- Hash pins: none in kit_k1a, k1_ops, or the top-level records in `distill_design/` (searched for cb0aadee, RUNCARD_K1, PROOFS.md).
- Line citations: `RUNCARD_K1.md:9` in `REFREEZE_PREREGISTRATION_20261115.md:65`, `.json:229`, `POLICY_AUDIT_20261115.md:30`. Original line 9 is a static template line (`finalize.py`, "Frozen settings: dense_aliases, ... step-544 private heads for one scale application and gravity ... boundaries.py."), so its text is recoverable verbatim.
- Generator: `kit_k1a/work/finalize.py` (RUNCARD at :46, PROOFS at :106-111). Inputs: `out/CAPTURES.json` (present, sha dde9aae9 = prereg pin), `out/K1_MANIFEST.template.json`, `out/K1_PLAN_RESULT.json`, `out/P{1..7},KIT,HANDOFF_RESULT.json` (all absent on 1-18), and `import bindings` from `orch_cd/o3_cache/work/kit` (absent on 1-18). finalize.py cannot run here, and running it would also overwrite `out/DEPENDENCIES.json` (the 108 pins verify_sources.py checks), STAGING_REQUIREMENTS.json, HEAVY_IO_QUESTION.md, DESIGN_RECORD*.md and the lane STATUS.md. Do not rerun it.
- Replacements (lane folder, first line says each replaces a lost original): `work/RUNCARD_K1.md` (finalize.py template verbatim; 7 lost values marked `[NOT RECOVERED: expr]`: unresolved dense captures, GPU-hour low/high, geometry hours, SAM hours low/high, prompt calls; cited line 9 is line 10 here) and `work/PROOFS.md` (9 proof statuses and 5 P2 numbers marked `[NOT RECOVERED]`; no proof rerun). Caveat: I cannot verify that kit_k1a's finalize.py is byte-identical to the b6_build copy that wrote the originals.

## (b) Every place that pins or checks the rules hash, and its regeneration
| Place | What | Regenerates by |
|---|---|---|
| REFREEZE_PREREGISTRATION_20261115.json:10, :55; .md:67 | full / prefix sha | unchanged; matches |
| kit_k1a/out/K1_RULES.sha256 | lost | `preregister.py` (writes the json only if absent, else asserts equality; then writes .sha256) |
| kit_k1a/work/k1_report.py:73 | refuses unless file == RULES and sha == .sha256 | runtime check; no regeneration |
| kit_k1a/work/audit_delivery.py:13, out/DELIVERY_AUDIT.json `rules_sha256` | lost audit | audit_delivery.py, which also needs the lost P*_RESULT.json files |
| K1_RESULT.json `rules_sha256` (k1_report.py:79) | future output | written by the K1 analysis |
| distill_design/RECOVERY_MAP_2_18_OUTAGE_20261115.md:58 | says a byte-exact rebuild is impossible | record owner's edit; now false |
No manifest (K1_MANIFEST.*), DEPENDENCIES.json, T1_SHA256SUMS or bootstrap file pins the rules hash.

## Kit gap found on the way
`k1_report.py:6` imports `official_mra` from `orch_cd/o3_cache/work/kit/vendor_sam/vendor`, absent on 1-18. Unshimmed, `k1_report.py` and `preregister.py` fail at import on this node. `kit_k1a/native_kit/vendor_sam/vendor/score_and_aggregate_orchard.py` (sha 0bb536ca, pinned in DEPENDENCIES.json:48) is the only copy; its identity with the o3_cache original is unverified.
