<!-- recovered by seal_plan: transcript=71f94277 line=24261 utc=2026-11-13T19:25:10.988Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_tree/inbox/$(date_ORCH_NOTE_init_artifact_is_retained.md heredoc_quoted -->
# ORCH note: the original-init artifact is retained; record the pointer and move on

Your 1923Z RESULT. The parent CP1 m200 init mirror is on Orchard and was re-hashed there today: operator RESULT of 10:03Z (workbench job 168962, read-only step): `artifact.json` c1a42588, `heads.pt` (2.76 GB), the full-weights manifest and six of six pinned files (18.8 GB) all match. The same checkpoint also exists on Trinity, where the eval lane reads it (its official and dev reads of CP1 m200). So the artifact's bytes are not at risk from the running job's end.

For the warm-start design note: cite the operator's 10:03Z RESULT (in `/scratch/jjyeung/orch_cd/orchard_cp2/events/`, the file of 2026-11-13 around 1003Z) as the retention evidence, and list "confirm the init artifact's sha at the path the new kit stages" as a seal-time check. Nothing else is needed now.

Next for you, in order: the G1 to G4 fixes of my 1908Z order; the comparison of your local routing and VQA digests with the production scan when the operator returns it; then the frame-pin cache.