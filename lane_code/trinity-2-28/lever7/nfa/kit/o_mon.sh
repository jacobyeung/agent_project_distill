#!/bin/bash
set -uo pipefail
P=/project/community/jjyeung/c8b836b4ae536
job=$(cat "$P/a/70.txt"); [[ "$job" =~ ^[0-9]+$ ]] || exit 1
TZ=UTC sacct -j "$job" -X -n -P -o JobID,State,Elapsed,NodeList,Start
st=$(squeue -j "$job" -h -o '%T' 2>/dev/null)
if [ "$st" = RUNNING ]; then
  timeout 60 srun --overlap --jobid "$job" -n1 bash -c 'R=/tmp/a'"$job"'c8b836b4ae536/sj/b01ec87a6f29b/r/metadata; for f in $R/reads/*/metadata/journals/*/0/items.jsonl; do [ -f "$f" ] && echo "${f#$R/} $(wc -l < "$f")"; done; ls $R 2>/dev/null | tr "\n" " "; echo'
fi
