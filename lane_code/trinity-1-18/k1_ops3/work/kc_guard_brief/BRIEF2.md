# Codex build k1_guard2: two review fixes to the k1_guard build (same workspace)

Workspace: /scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard (your previous build; your report is ../kc_guard_brief/REPORT.md). Same rules as ../kc_guard_brief/BRIEF.md (read it): write only in kc_guard, kc_guard_brief, kc_guard_tests; no ssh, git, kill, network, GPU, deletion; k1_phases.py, every B.source_identity() file and manifest v2 stay byte-equal. Read-only: the reviewer's verdict /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_k1c/REVIEW_VERDICT_K1C.md and its forge test /scratch/jjyeung/orch_n30/review_k1c/work/kc_guard_tests/rev_forge.py (copy it into kc_guard_tests to run it; do not write in the reviewer's folder).

## Fix 1 (forged refusal accepted)
cached() (k1_pipeline.py ~101-103) trusts a refusal receipt's verdict via k1_guard.restore_verdict; check_receipt (k1_guard.py ~57-58) makes REFUSED_GEOMETRY.npz optional. Make a refusal receipt require REFUSED_GEOMETRY.npz (pinned), and inside the guard capture context re-run load_geometry on that file, require GeometryError('reference_camera_up_opposes_gravity') from the installed reviewed guard, and require the re-derived verdict == receipt['gravity_verdict'] (else raise and halt). The reviewer verified this re-derivation reproduces the planted refusal's verdict (True, True). Also make convert's resume path use the same check. rev_forge.py must now fail closed (both forged variants rejected). Passing and planted-refusal tests must still pass.

## Fix 2 (downstream interpreter)
kc_guard_brief/k1_downstream.guard.sh sets PY=sam3_scipy_ovl; restore PY=/scratch/jjyeung/envs/p1cpu/bin/python exactly as the original /scratch/jjyeung/orch_n30/k1_ops3/work/k1_downstream.sh line 13. Show that p1cpu runs cached() (passing canary capture and the planted refusal) and the tables/render fixture tests under the guard. convert7.guard.sh keeps sam3_scipy_ovl.

## Then
Update the sha256 lines in both launchers for changed files; rerun test_k1_guard.py (plus a new test for fix 1), the identity proof (verify_identity.py), the real canary convert into a fresh test root, test_kit/test_guards/verify_sources. Append a section "Fixes after review_k1c" to REPORT.md (diff, new shas, test outputs) and write PATCH2.diff (changes since the first build). End with READY or NOT READY.
