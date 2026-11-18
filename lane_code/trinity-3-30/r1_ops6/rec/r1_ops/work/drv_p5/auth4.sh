export TZ=UTC
O=/project/community/jjyeung/okh7
for f in $O/x_69d2930d/k/4.json $O/x_3fdda0fb/k/4.json $O/x_69d2930d.f170956/k/4.json; do echo "== $f"; python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print({k:d.get(k) for k in ('modes','new_gpus','resume','allowed_partitions','allow_until_utc','arm','gpu_cap','other_running_and_pending_gpus','production_go_granted')})" $f 2>&1 | cut -c1-400; ls -la --time-style=+%m-%dT%H:%M $f; done
ls $O/x_3fdda0fb/k | head -50 | tr '\n' ' '
