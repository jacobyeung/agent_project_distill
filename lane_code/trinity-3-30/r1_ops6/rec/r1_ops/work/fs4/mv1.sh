#!/bin/bash
# r1_ops4: move proof 171356's bundle markers aside (cancelled by ORCH 0541Z), then emit 171377 metrics (base64 tar).
set +x; set -uo pipefail; export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; BUN=$O/i_69d2930d
fresh() { [[ ! -e "$1" && ! -L "$1" ]]; }
ok=1
[[ "$(cat "$BUN/job.id" 2>/dev/null)" == 171356 ]] || { echo "REFUSED: job.id is not 171356"; ok=0; }
[[ -z "$(squeue -h -j 171356 -o %i 2>/dev/null)" ]] || { echo "REFUSED: 171356 still queued"; ok=0; }
st=$(sacct -X -n -P -j 171356 -o State | head -1); [[ "$st" == CANCELLED* ]] || { echo "REFUSED: 171356 state $st"; ok=0; }
if [[ $ok == 1 ]]; then
 for f in job.id sbatch.out submission.started a.json; do
  if [[ -f "$BUN/$f" && ! -L "$BUN/$f" ]] && fresh "$BUN/$f.a2_171356"; then mv -n -- "$BUN/$f" "$BUN/$f.a2_171356" && echo "moved $f"; else echo "skip $f"; fi
 done
 ls -la $BUN | grep -E 'a1_|a2_|job.id|sbatch|submission|a.json' | awk '{print $5,$NF}'
fi
echo "== proof.json"; python3 -c "import json;d=json.load(open('$O/x_69d2930d/o/171356.proof.json'));print(d.get('status'),list(d)[:20])" 2>&1 | head -3
R=$O/x_69d2930d/runs/673bc60f
echo "B64:"; cd $R && tar czf - attempt_171377.json metrics_171377.jsonl | base64 -w0
