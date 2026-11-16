<!-- recovered by seal_plan: transcript=a97ad692 line=3071 utc=2026-11-15T09:01:03.842Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > $R/official544/inbox/${T}_ORCH_ANSWER_revsi_media_root.md <<'EOF'
# ORCH ANSWER to your 0900Z question

Your default stands: finish CPU validation and seal the ReVSI reader, with the production launcher input fail-closed until the Orchard owner lane supplies an opaque media root for the 32-frame tier. I have asked that lane to find or stage it (it will write the root and its hash check into your inbox). Give it, in one note in its inbox, the exact list it must stage: the 261 catalogue entries the five-category cohort uses, each with its sha256 and size, and the durable source path of the tier. Do not copy media yourself.
EOF
cat > $R/evalx/inbox/${T}_ORCH_QUEUE_revsi32_media_root.md <<EOF
# ORCH QUEUE ITEM (after the VSI-Bench direct packet; not urgent): an opaque Orchard root for the ReVSI 32-frame videos

Lane official544 is sealing a ReVSI direct read of the step-544 model on the five categories it answers directly (\`$R/official544/events/20261115T0900Z_QUESTION_revsi32_owner_media_alias.md\`). It needs the 32-frame tier's videos on Orchard under an opaque root: 302 catalogue entries, 365,324,049 bytes, of which the cohort uses 261. It will put the exact list with hashes and the durable source path into your inbox.
1. From local records first: is that tier already on Orchard (the parent model's ReVSI reads of 2026-11-12 ran somewhere: check where and what they staged)? If yes, one alias call as before, with a count and byte check against the list.
2. If not: propose one governed stream of one archive of the 261 files (about 0.3 GB) from the durable source through the governor to an opaque root, then per-file hash checks there. It waits its turn in the governor like any other. Tell me the plan in one line before registering it; no Orchard call and no stream before my word.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) official544 QUESTION 0900Z: the ReVSI 32-frame kit works on CPU (five categories, label-free); it needs an opaque Orchard media root (302 entries, 365 MB; cohort uses 261). Answered: default stands (fail-closed until the owner supplies the root); queued the item for evalx (find an existing Orchard copy or propose one governed stream; my word before any call)." >> $R/ORCH_HANDOFF.md