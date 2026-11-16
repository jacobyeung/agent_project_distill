<!-- recovered by seal_plan: transcript=71f94277 line=34902 utc=2026-11-15T03:05:22.317Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ANSWER_frame_fixtures_for_rehearsal.md <<'EOF'
# ORCH answer: use tiny pinned PNG fixtures for frame bytes; keep the verification code real

I know of no local copy of the dev frames on this node and will not have one fetched for a rehearsal. Frame bytes are a third stand-in boundary, beside the model and the tower:

- Build a rehearsal-only frame store of tiny PNGs, one per wanted frame name, with their own hashes, and a rehearsal-only request whose frame pins are those hashes. The real `trainer_row(..., verify=True)`, the membership checks and the mask admission run unchanged against it, so every line of that code executes; only the image content is synthetic.
- Rehearsal pins never enter a sealed family or a packet. Keep the fixture store and the rehearsal request under a folder whose name says so, and have the family's packaging refuse any request that carries them (a test, if it is not already impossible by construction).
- In the coverage report, name the three stand-in boundaries (model and decode, tower geometry, frame bytes) and state for the third that the real frame pins were verified on the real node by pilots 169605, 169670 and 169687 (P3 passed), after checking that the frame pins of the new family equal theirs.
- Keep the fixture store small (a few MB).

Proceed without further questions on stand-ins; anything else that would need a download, a weaker check or a new stand-in comes to me.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) QUESTION 0304Z: the CPU rehearsal needs frame PNGs (Orchard-only). Answered: tiny pinned PNG fixtures as a third stand-in boundary (rehearsal-only request; verification code real; real frame pins covered by pilots 6-8's P3 with equal pins)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md