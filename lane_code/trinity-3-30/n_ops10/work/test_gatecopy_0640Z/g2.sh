# n_ops10 fallback (ORCH ANSWER 0630Z item 3): copy the six node-local gate files of job 990001 once into X/o/990001_gate_f/
J=990001; X=/scratch/jjyeung/orch_n30/n_ops10/work/test_gatecopy_0640Z/x
# fires unless jn6's copy is complete (SHA256SUMS with 6 lines and no NOTES.txt; review note N1); never touches jn6's dir, writes X/o/<J>_gate_f/
G0=$X/o/${J}_gate; nl=$(cat $G0/SHA256SUMS 2>/dev/null | wc -l)
if [ "$nl" -ge 6 ] && [ ! -e $G0/NOTES.txt ]; then echo "GATECOPY skip: $G0 complete ($nl lines)"; ls -la $G0
elif [ -e $X/o/${J}_gate_f/SHA256SUMS ]; then echo "GATECOPY skip: fallback already done"; cat $X/o/${J}_gate_f/SHA256SUMS; else
echo "GATECOPY start: jn6 copy lines=$nl notes=$(cat $G0/NOTES.txt 2>/dev/null | head -3 | tr '\n' ';')"
timeout 120 srun --overlap --jobid=$J -N1 -n1 --mem=1G bash -c '
J='$J'; X='$X'; N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_$J"; [ -d "$N" ] || N=/tmp/q_22c714e1_$J
G=$X/o/${J}_gate_f; cd "$N/p/q" || { echo "GATECOPY FAIL no $N/p/q"; exit 3; }
F="b/population.json b/indices.json b/reader_filters.json b/binding.json b/receipt.json f.json"
tot=0; for f in $F; do [ -f "$f" ] && tot=$((tot+$(stat -c %s "$f"))); done; echo "GATECOPY N=$N raw_total=$tot"
mkdir -p -m 700 "$G"; chmod 700 "$G"; : > "$G/SHA256SUMS.part"
for f in $F; do b=$(echo $f | tr / _)
  if [ ! -f "$f" ]; then echo "MISSING $f" | tee -a "$G/NOTES.txt"; continue; fi
  gz=$(gzip -9 -c "$f" | wc -c); if [ $gz -gt 10000000 ]; then echo "SKIP $f gz=$gz > 10 MB" | tee -a "$G/NOTES.txt"; continue; fi
  gzip -9 -c "$f" > "$G/$b.gz.part" && mv "$G/$b.gz.part" "$G/$b.gz"; sha256sum "$f" >> "$G/SHA256SUMS.part"; done
mv "$G/SHA256SUMS.part" "$G/SHA256SUMS"; cat "$G/SHA256SUMS"; ls -la "$G"' < /dev/null 2>&1 | tail -20; fi
