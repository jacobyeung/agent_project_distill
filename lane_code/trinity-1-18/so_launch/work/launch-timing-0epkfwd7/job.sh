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
export TK_JOB_START="${TK_JOB_START:-$(date +%s)}"
ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
tk_job_timing() {
    [[ "${TK_LAUNCH_TIMING:-0}" == 1 ]] || return 0
    [[ -d "$ROOT/o" ]] || return 0
    { printf '%s | job phase %s\n' "$(date -u +%FT%TZ)" "$1" >> "$ROOT/o/${SLURM_JOB_ID:-local}.steps"; } 2>/dev/null || true
}
tk_job_timing capsule_start
/usr/bin/python3 -B "$ROOT/b/a.py" "$ROOT"
tk_job_timing capsule_done
tk_job_timing import_preflight_start
/bin/bash "$ROOT/b/p0.sh" "$ROOT"
tk_job_timing import_preflight_done
tk_job_timing launch_guard_start
/usr/bin/python3 -I "$ROOT/b/g.py" "$ROOT" p
tk_job_timing launch_guard_done
RUN="$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$ROOT/k/launch.json")"
tk_job_timing resume_choice_start
MODE="$(/usr/bin/python3 -I "$ROOT/b/r8.py" "$RUN" --kit "$ROOT")"
tk_job_timing resume_choice_done
tk_job_timing dispatch_start
exec /bin/bash "$ROOT/b/r.sh" "$MODE" 0
