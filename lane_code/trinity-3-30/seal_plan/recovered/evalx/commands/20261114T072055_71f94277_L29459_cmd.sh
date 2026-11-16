<!-- recovered by seal_plan: transcript=71f94277 line=29459 utc=2026-11-14T07:20:55.864Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_AUTHORIZED_stop_archive_names.md <<'EOF'
# ORCH answer to BLOCKER 0720Z: authorized; the stop route admits the producer's three stop-object names

Good catch, seven hours before it mattered. Authorized, as one small diff on the confirmed pins (reader b8ebab38, `release_check.py` 19197a81, launcher digest 555eb739):

- In the stop-export route only, the archive identity may be `q8/8865619b/469ddece_mstop.tar`, `..._mstopB.tar` or `..._mstopC.tar` with its four matching parts, instead of `..._mN.tar`. The operator's attestation must name which of the three the producer selected and carry the step from the producer's claim file (the operator reads that claim, at most 64 bytes, and it must equal the artifact's own step) together with `stop_export: true`. Bind in the check: the selected object name, the claim's step, the artifact's step and the transport pin all agree.
- The milestone route is unchanged: a registered milestone still requires `..._mN.tar`, and a stop-object name is refused there. A numbered name is refused in the stop route.
- Tests: the three stop names pass with a consistent attestation; each fails when the claim step, the artifact step or the selected name disagrees; a stop name in the milestone route refuses; `_m560.tar` in the stop route refuses.

Send the diff, the new hashes (reader unchanged unless it must change; say so), the launcher digest and the test counts. I confirm by reading the diff. Agree the attestation's field names with orchard_cp2 through its inbox now, so its stop attestor and your check match; tell me only if you disagree on a field.

This sits behind the uploads, the seal and the P0 submission in your order of work, but must be confirmed by 13:00Z.
EOF
cat > $C/orchard_cp2/inbox/${N}_ORCH_NOTE_stop_transport_contract.md <<'EOF'
# ORCH note: the stop export's transport contract

evalx's admitted check requires a numbered archive name today; I have authorized it to admit the producer's three stop-object names (`469ddece_mstop.tar`, `mstopB.tar`, `mstopC.tar`) in the stop route, bound to: the object name the producer selected, the step from the producer's claim file (your bounded read), the artifact's own step, and the transport pin, with `stop_export: true`. Agree the attestation's exact field names with evalx through its inbox; your stop attestor should emit exactly what its check reads. Tell me only if the two of you disagree on a field.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: evalx(21) BLOCKER 0720Z: the confirmed release_check.verify() requires archive names q8/8865619b/469ddece_mN.tar, but the producer's stop export is named 469ddece_mstop{,B,C}.tar, so the final read would be refused at transport admission (CPU reproduction evalx/out/STOP_TRANSPORT_CONTRACT_S21.json). AUTHORIZED ($N): the stop route admits the three stop-object names bound to the selected name, the claim's step, the artifact's step and the transport pin; milestone route unchanged; tests; one diff for my confirmation by 13:00Z; field names agreed with orchard_cp2 directly. Re-armed evwait (b4uklsj37)." >> $C/ORCH_HANDOFF.md