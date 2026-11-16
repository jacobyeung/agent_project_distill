#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:USR1@3600
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
export TK_JOB_START="$(date +%s)"
ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
/usr/bin/python3 -B "$ROOT/b/a.py" "$ROOT"
/usr/bin/python3 -I "$ROOT/b/g.py" "$ROOT" p
RUN="$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$ROOT/k/launch.json")"
MODE="$(/usr/bin/python3 -I "$ROOT/b/r8.py" "$RUN" --kit "$ROOT")"
exec /bin/bash "$ROOT/b/r.sh" "$MODE" 0
