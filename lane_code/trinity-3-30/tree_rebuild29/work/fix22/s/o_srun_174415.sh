export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=174415; D=$X/o/${J}_x
test ! -e $D || { echo EXISTS; exit 1; }; mkdir -m 700 $D
cat > $D/w.sh <<'EOW'
#!/bin/bash
# read-only: wait for two node-local json files of job 174415, copy them once; at most 30 min
D=/project/community/jjyeung/okh7/x_22c714e1/o/174415_x
for b in "${SLURM_TMPDIR:-/tmp}" /tmp; do N=$b/q_22c714e1_174415; [ -d "$N" ] && break; done
echo "N=$N $(date -u +%TZ)"
for i in $(seq 1 120); do
  ok=1
  for f in dr/p/q/selection/pool/relocation.json dr/p/i/pool/c.json; do
    t=$D/k_$(echo $f | tr / _); [ -e "$t" ] && continue
    if [ -f "$N/$f" ] && [ "$(find "$N/$f" -mmin +0.5 2>/dev/null)" ]; then cp "$N/$f" "$t.part" && mv "$t.part" "$t" && echo "copied $f $(sha256sum "$t" | cut -c1-64) $(stat -c %s "$t") $(date -u +%TZ)"; else ok=0; fi
  done
  [ $ok = 1 ] && { echo DONE; exit 0; }
  sleep 15
done
echo TIMEOUT
EOW
chmod 700 $D/w.sh
nohup srun --overlap --jobid=$J -N1 -n1 --cpus-per-task=1 --mem=1G $D/w.sh > $D/w.log 2>&1 &
sleep 20; cat $D/w.log; squeue -s -j $J -h -o "%i %j %T" 2>&1 | head
