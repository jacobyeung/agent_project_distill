export TZ=UTC
# yield rule (ORCH 1359Z): our general read ids in OURS (space-separated); cancel them if a jjy_* job is PENDING on general with QOSMaxJobsPerUserLimit
G=$(squeue -u jjyeung -p general -h -o "%i %j %T %r" 2>&1); echo "$G" | sed 's/^/GEN /'
if [ -n "${OURS:-}" ]; then
  MP=$(echo "$G" | awk '$2 ~ /^jjy_/ && $3=="PENDING" && $4 ~ /QOSMaxJobsPerUser/')
  RUN=""; for j in $OURS; do echo "$G" | awk -v j=$j '$1==j' | grep -q . && RUN="$RUN $j"; done
  if [ -n "$MP" ] && [ -n "$RUN" ]; then scancel $RUN; echo "YIELD_CANCELLED$RUN at $(date -u +%TZ) rc=$? because: $MP"; fi
fi
