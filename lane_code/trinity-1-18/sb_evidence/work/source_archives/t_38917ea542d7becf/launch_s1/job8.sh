#!/bin/bash
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-task=96
#SBATCH --mem=1600G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:USR1@900
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
/usr/bin/python3 -B "$ROOT/b/a.py" "$ROOT"
/usr/bin/python3 -I "$ROOT/b/g.py" "$ROOT"
RUN="$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$ROOT/k/launch.json")"
MODE="$(/usr/bin/python3 -I "$ROOT/b/r8.py" "$RUN" --kit "$ROOT")"
exec /bin/bash "$ROOT/b/r.sh" "$MODE" 0
