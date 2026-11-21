TZ=UTC date +%TZ
timeout 200 srun --overlap --jobid 174134 -N1 -n1 nice -n 15 bash -c '
D=/tmp/a15_dbg_174134; find $D -maxdepth 5 -type f -size -400M 2>/dev/null | grep -v -E "/s/|\.py$|triton|__pycache__|/frames?/" | head -80 | while read f; do echo "$(stat -c %s $f) $f"; done
python3 -c "import json;d=json.load(open(\"$D/mixc.json\"));print(type(d).__name__, list(d)[:20] if isinstance(d,dict) else len(d)); print(json.dumps(d)[:800])"
' < /dev/null
