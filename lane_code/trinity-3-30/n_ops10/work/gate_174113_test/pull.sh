# n_ops10 gate route (ORCH ORDER 1055Z item 1): stream node-local files of job 174113 to Trinity with no byte written to /project.
# Runs on the Orchard login node through ossh 'bash -s'; stdout = one tar.gz (SHA256SUMS of the raw files computed on the node + the files); everything else goes to stderr.
# MODE test: q.steps only. MODE gate: the six gate files + node-local live receipts (N/ev/live, N/live_spool if present) + X/o/<job>/live (read only).
J=174113; MODE=test; X=/project/community/jjyeung/okh7/x_22c714e1
timeout 240 srun --overlap --jobid=$J -N1 -n1 --mem=1G bash -c '
J='$J'; MODE='$MODE'; X='$X'
N=/tmp/q_22c714e1_$J; [ -d "$N" ] || N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_$J"
T=/tmp/n10pull_$J; mkdir -p -m 700 $T; : > $T/SHA256SUMS; : > $T/LIST
if [ "$MODE" = test ]; then for f in "$N/q.steps"; do [ -f "$f" ] && echo "$f" >> $T/LIST; done
else
  for f in p/q/b/population.json p/q/b/indices.json p/q/b/reader_filters.json p/q/b/binding.json p/q/b/receipt.json p/q/f.json; do
    if [ -f "$N/$f" ]; then echo "$N/$f" >> $T/LIST; else echo "MISSING $N/$f" >&2; echo "MISSING $N/$f" >> $T/NOTES; fi; done
  for d in "$N/ev/live" "$N/live_spool" "$X/o/$J/live"; do [ -d "$d" ] && find "$d" -maxdepth 1 -type f -size -20M >> $T/LIST; done
fi
while read -r f; do r=${f#/}; ( cd / && sha256sum "$r" ) >> $T/SHA256SUMS; done < $T/LIST
echo "PULL host=$(hostname -s) N=$N files=$(wc -l < $T/LIST) bytes=$(cat $T/LIST | xargs -r stat -c %s | awk "{s+=\$1} END{print s}")" >&2
sed "s#^/##" $T/LIST > $T/REL
tar czf - -C $T SHA256SUMS LIST $( [ -f $T/NOTES ] && echo NOTES ) -C / -T $T/REL
' < /dev/null
