export TZ=UTC; date -u +%TZ
timeout 120 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
cd /tmp/a15_f16_174198/w1 || exit 3
L=""
for f in w/live/* w/top/tb.txt w/top/p/q/RESULT.json w/top/p/q/host.json w/top/p/q/f.json w/top/p/q/b/* w/top/p/q/p/request.json w/top/p/q/p/phase_*.complete.json w/top/p/q/p/data_receipt.json \
  w/top/p/q/p/frames_*/frames.json w/top/p/q/p/frames_*/result.json \
  w/top/p/q/p/prepare_*/config.json w/top/p/q/p/prepare_*/result.json w/top/p/q/p/prepare_*/parent_grounding.json w/top/p/q/p/prepare_*/handover.json \
  w/top/p/q/p/prepare_*/prepared/receipt.json w/top/p/q/p/prepare_*/prepared/s1_receipt.json \
  w/top/p/q/p/prepare_*/routing/receipt.json w/top/p/q/p/prepare_*/routing/materialization.json w/top/p/q/p/prepare_*/pointing/receipt.json w/top/p/q/p/prepare_*/vqa/receipt.json \
  w/top/p/q/selection/receipt.json w/top/p/q/selection/materialization.json w/top/p/q/twins/room_audit.json w/top/p/q/twins/receipt.json w/top/p/q/twins/augmentation.json \
  w/top/p/q/v.json w/top/p/q/m.json w/top/p/q/c.json w/top/p/q/n.json w/top/p/q/e.json w/top/p/q/ss.json \
  log/go.log log/q.log log/q.err log/stop.log log/bwrap_args.txt; do
  [ -f "$f" ] && [ ! -L "$f" ] && [ "$(stat -c %s "$f")" -lt 4000000 ] && L="$L $f"
done
echo "PULL $(date -u +%TZ) files $(echo $L | wc -w) bytes $(du -cb $L | tail -1 | cut -f1); live folder: $(ls w/live | tr '\n' ' ')"
for f in $L; do echo "SUM $(sha256sum "$f" | cut -c1-64) $(stat -c %s "$f") $f"; done
echo "===B64==="; tar czf - $L | base64 -w 76; echo "===END==="
EOS
date -u +%TZ
