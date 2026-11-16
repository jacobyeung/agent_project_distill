P=/project/community/jjyeung
for py in $P/cp4tk_fr/venv/bin/python3 $P/45e92888780e/envs/*/bin/python3 $P/orchard_data/envs/*/bin/python3 $P/orchard_next/env/bin/python3 $P/latency/envs/*/bin/python3; do
  [ -x "$py" ] || continue
  echo "== $py"; timeout 120 nice -n 19 "$py" -c 'import torch,numpy,sys;print(sys.version.split()[0],torch.__version__,numpy.__version__)' 2>&1 | tail -1
done
