# n_ops10 fallback (ORCH ANSWER 0630Z item 3): copy the six node-local gate files of job __J__ once into X/o/__J___gate/
J=__J__; X=/project/community/jjyeung/okh7/x_22c714e1
if [ -e $X/o/${J}_gate/SHA256SUMS ]; then echo "GATECOPY skip: $X/o/${J}_gate/SHA256SUMS exists"; else
timeout 120 srun --overlap --jobid=$J -N1 -n1 --mem=1G bash -c '
J='$J'; X='$X'; N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_$J"; [ -d "$N" ] || N=/tmp/q_22c714e1_$J
G=$X/o/${J}_gate; cd "$N/p/q" || { echo "GATECOPY FAIL no $N/p/q"; exit 3; }
F="b/population.json b/indices.json b/reader_filters.json b/binding.json b/receipt.json f.json"
tot=0; for f in $F; do [ -f "$f" ] && tot=$((tot+$(stat -c %s "$f"))); done; echo "GATECOPY N=$N raw_total=$tot"
mkdir -p -m 700 "$G"; chmod 700 "$G"; : > "$G/SHA256SUMS.part"
for f in $F; do b=$(echo $f | tr / _)
  if [ ! -f "$f" ]; then echo "MISSING $f" | tee -a "$G/NOTES.txt"; continue; fi
  gz=$(gzip -9 -c "$f" | wc -c); if [ $gz -gt 10000000 ]; then echo "SKIP $f gz=$gz > 10 MB" | tee -a "$G/NOTES.txt"; continue; fi
  gzip -9 -c "$f" > "$G/$b.gz.part" && mv "$G/$b.gz.part" "$G/$b.gz"; sha256sum "$f" >> "$G/SHA256SUMS.part"; done
mv "$G/SHA256SUMS.part" "$G/SHA256SUMS"; cat "$G/SHA256SUMS"; ls -la "$G"' < /dev/null 2>&1 | tail -20; fi
