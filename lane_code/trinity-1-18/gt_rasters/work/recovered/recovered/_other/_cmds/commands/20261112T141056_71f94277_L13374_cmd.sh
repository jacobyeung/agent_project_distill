<!-- recovered by seal_plan: transcript=71f94277 line=13374 utc=2026-11-12T14:10:56.318Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; D=$(date -u +%FT%TZ); cat > $M/codex-token-economy-20261112.md <<EOF
---
name: codex-token-economy-20261112
description: "USER 2026-11-12: do not waste Codex tokens; dispatch a Codex lane only when a launch, a decision or a queued GPU run depends on its output"
metadata:
  type: feedback
---

USER, 2026-11-12 (~$D), verbatim: "By the way, if you don't need to burn Codex tokens, don't waste them." It came after I had dispatched five Codex lanes in two hours (next-leg code and its second pass, two grounding kits, a mask-recall kit, a small scorer-test lane) while the leg's launch was blocked.

**Why:** Codex usage costs the user; pre-building is wanted ([[build-experiments-first]]), but only where the output will be used.

**How to apply (my reading):** before a Codex dispatch, name the launch, decision or queued GPU run that needs its output within about a day; if there is none, do not dispatch. Fold small fixes into a lane that is already running or into the next required pass instead of a lane of their own. Prefer one well-scoped pass over a pass plus a repair pass: ask in the first brief for what the reviewer will check. Do not stop a lane that is mid-run just to save tokens; its spent tokens would be lost.
EOF
echo "- **READ FIRST, USER 11-12:** [Do not waste Codex tokens](codex-token-economy-20261112.md) dispatch Codex only when a launch, decision or queued GPU run needs the output; fold small fixes into running lanes" >> $M/MEMORY.md; echo "$D orch-home-distill-79: USER: 'if you don't need to burn Codex tokens, don't waste them' -> memory codex-token-economy-20261112.md; no new Codex lanes unless a launch/decision/queued run needs the output; leg_s2_p2 (running) finishes." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; tmux ls 2>/dev/null | grep cx_ | cut -c1-40