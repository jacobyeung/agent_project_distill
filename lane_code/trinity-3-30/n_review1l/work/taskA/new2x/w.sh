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
