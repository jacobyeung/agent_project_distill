export TZ=UTC; date -u +%TZ
timeout 150 srun --overlap --jobid 174246 -N1 -n1 bash -s <<'EOS'
J=/tmp/q_22c714e1_174246; U=$J/s/aws/u
for f in ap/97a6a3eb/runs/b19c1200/train/step_400/encoder.safetensors ap/97a6a3eb/runs/b19c1200/train/step_400/heads.safetensors ap/8865619b/runs/6ed2c7aa/m400/full_weights/full_weights.json; do
  p=$U/$f; if [ -e "$p" ]; then echo "PRESENT $(stat -L -c %s "$p") B $( [ -L "$p" ] && echo "symlink->$(readlink "$p")") $f"; else echo "ABSENT $f"; fi
done
ls -la $J/rp 2>&1 | head -5
f=$U/ap/97a6a3eb/runs/b19c1200/train/step_400/heads.safetensors; [ -f "$f" ] && [ $(stat -L -c %s "$f") -lt 2000000000 ] && echo "heads sha $(sha256sum "$f" | cut -c1-16)"
EOS
date -u +%TZ
