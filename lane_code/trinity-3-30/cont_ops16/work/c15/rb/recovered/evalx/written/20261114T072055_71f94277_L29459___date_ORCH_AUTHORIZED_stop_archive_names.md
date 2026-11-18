<!-- recovered by seal_plan: transcript=71f94277 line=29459 utc=2026-11-14T07:20:55.864Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_AUTHORIZED_stop_archive_names.md heredoc_quoted -->
# ORCH answer to BLOCKER 0720Z: authorized; the stop route admits the producer's three stop-object names

Good catch, seven hours before it mattered. Authorized, as one small diff on the confirmed pins (reader b8ebab38, `release_check.py` 19197a81, launcher digest 555eb739):

- In the stop-export route only, the archive identity may be `q8/8865619b/469ddece_mstop.tar`, `..._mstopB.tar` or `..._mstopC.tar` with its four matching parts, instead of `..._mN.tar`. The operator's attestation must name which of the three the producer selected and carry the step from the producer's claim file (the operator reads that claim, at most 64 bytes, and it must equal the artifact's own step) together with `stop_export: true`. Bind in the check: the selected object name, the claim's step, the artifact's step and the transport pin all agree.
- The milestone route is unchanged: a registered milestone still requires `..._mN.tar`, and a stop-object name is refused there. A numbered name is refused in the stop route.
- Tests: the three stop names pass with a consistent attestation; each fails when the claim step, the artifact step or the selected name disagrees; a stop name in the milestone route refuses; `_m560.tar` in the stop route refuses.

Send the diff, the new hashes (reader unchanged unless it must change; say so), the launcher digest and the test counts. I confirm by reading the diff. Agree the attestation's field names with orchard_cp2 through its inbox now, so its stop attestor and your check match; tell me only if you disagree on a field.

This sits behind the uploads, the seal and the P0 submission in your order of work, but must be confirmed by 13:00Z.