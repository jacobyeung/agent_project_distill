<!-- recovered by seal_plan: transcript=71f94277 line=32787 utc=2026-11-14T17:42:27.108Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ANSWER_row_dispositions.md <<'EOF'
# ORCH answer: yes to both; four dispositions

Each of the 46 rows carries exactly one of these, and admission requires that none is blank:
1. **executed locally** on the freshly staged bytes;
2. **statically proved** (the pin is parsed and compared with the staged bytes);
3. **covered by a named earlier pilot** whose authenticated records show the check passing on identical inputs: the same object generation, archive hash and member manifest, each of which you verify against the current family. Pilot 169589's staging records and import hashes serve this way for the runtime, the base model, the export and the depth file; pilot 169521 for the restore chain;
4. **live only**: an identity that exists only after submission (job id, allocation, card, private mount). Record the predicate and the code line that enforces it in the job; leave the job's live check untouched.

No large copy, as you say. This is the same scheme as item 5 of my order of a few minutes ago, with disposition 4 added. Proceed without further questions on the scheme.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx QUESTION 1741Z (large production objects and future allocation identities in the pin list): answered: four dispositions per row (executed locally; statically proved; covered by a named earlier pilot on identical generations/hashes/manifests; live-only with the enforcing code line). No large copy." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md