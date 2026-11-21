#!/bin/bash
# usage: r.sh <this folder> <kit folder> [python of an already extracted kit environment]
# Reads: the kit folder (b/mg.py, SHA256SUMS.txt), the kit environment archive and the overlay archive named below.
# Writes: r.txt and e.txt in this folder; the environment under /tmp/a15_<token>_<job> on the node (left in place).
D=$1; K=$2; P=${3:-}; cd "$D" || exit 1
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
{ date -u +%FT%TZ; hostname; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>&1
  echo "seal $(sha256sum < "$K/SHA256SUMS.txt" | cut -c1-64)"; echo "guard $(sha256sum < "$K/b/mg.py" | cut -c1-64)"; } > r.txt
N="${SLURM_TMPDIR:-/tmp}/a15_e7c1a94b3d20_${SLURM_JOB_ID:-0}"; mkdir -p "$N"; export HF_HOME="$N/hf" XDG_CACHE_HOME="$N/cache" TMPDIR="$N"
if [ -z "$P" ]; then
  /usr/bin/python3 -B -I /project/community/jjyeung/okh7/x_ee227714/b/kitx.py /project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar \
    ffc81db4b3b1c3d1e42ac91159d504dc57b36eebfc75f537d15a426bbe6a8a22 "$N/v" >> r.txt 2>> e.txt || { echo ENV_FAIL >> r.txt; exit 3; }
  P="$N/v/rwtrain_torch211_cu129/bin/python"
fi
echo "== $P $(date -u +%TZ)" >> r.txt
O=""
if mkdir -p "$N/f" && tar -x -f /project/community/jjyeung/okh7/l_94a76bda/in/d00 -C "$N/f" --no-same-owner 2>> e.txt && (cd "$N/f/ebe69df8/p" && sha256sum -c --quiet ../m.sha) >> e.txt 2>&1; then O="$N/f/ebe69df8/p"; fi
echo "overlay ${O:+on}${O:-off}" | sed "s#$N#N#" >> r.txt
for c in none guard_import control_import guard_query control_query job_order_guard job_order_control; do
  PYTHONPATH="$O" timeout 100 "$P" -B -s "$D/t.py" "$c" "$K/b" >> r.txt 2> /dev/null; echo "rc $c $?" >> r.txt
done
date -u +%FT%TZ >> r.txt
