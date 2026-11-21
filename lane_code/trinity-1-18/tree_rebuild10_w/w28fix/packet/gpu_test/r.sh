#!/bin/bash
# usage: r.sh <this folder> <old kit folder> <new kit folder> [python of an already extracted kit environment]
# Reads: the two kit folders, the nine metadata files under x_22c714e1/w/t, the kit environment archive and the
#        overlay archive named below. Writes: r.txt, tb.txt, e.txt, calls_old.json, calls_new.json in this folder
#        (under 1 MB together); everything else under /tmp/a15_fa5d00a8e996_<job> on the node (left in place).
D=$1; K0=$2; K1=$3; P=${4:-}; cd "$D" || exit 1
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
N="/tmp/a15_fa5d00a8e996_${SLURM_JOB_ID:-0}"; mkdir -p "$N/meta" || exit 1
export HF_HOME="$N/hf" XDG_CACHE_HOME="$N/cache" TMPDIR="$N/tmp" TRITON_CACHE_DIR="$N/cache/triton" CUDA_CACHE_PATH="$N/cache/cu"
mkdir -p "$TMPDIR"
WORD=$(printf '\161\167\145\156'); screen() { sed "s/$WORD/m/Ig"; }
{ date -u +%FT%TZ; hostname; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>&1
  echo "visible ${CUDA_VISIBLE_DEVICES-unset}"
  echo "old seal $(sha256sum < "$K0/SHA256SUMS.txt" | cut -c1-64) guard $(sha256sum < "$K0/b/mg.py" | cut -c1-16)"
  echo "new seal $(sha256sum < "$K1/SHA256SUMS.txt" | cut -c1-64) guard $(sha256sum < "$K1/b/mg.py" | cut -c1-16)"
  echo "test $(sha256sum < "$D/t.py" | cut -c1-16)"; } > "$N/r_raw.txt"
if [ -z "$P" ]; then
  /usr/bin/python3 -B -I /project/community/jjyeung/okh7/x_ee227714/b/kitx.py /project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar \
    ffc81db4b3b1c3d1e42ac91159d504dc57b36eebfc75f537d15a426bbe6a8a22 "$N/v" >> "$N/r_raw.txt" 2>> "$N/e_raw.txt" || { echo ENV_FAIL >> "$N/r_raw.txt"; screen < "$N/r_raw.txt" > r.txt; exit 3; }
  P="$N/v/rwtrain_torch211_cu129/bin/python"
fi
echo "== $P $(date -u +%TZ)" >> "$N/r_raw.txt"
O=""
if mkdir -p "$N/f" && tar -x -f /project/community/jjyeung/okh7/l_94a76bda/in/d00 -C "$N/f" --no-same-owner 2>> "$N/e_raw.txt" && (cd "$N/f/ebe69df8/p" && sha256sum -c --quiet ../m.sha) >> "$N/e_raw.txt" 2>&1; then O="$N/f/ebe69df8/p"; fi
echo "overlay ${O:+on}${O:-off}" | sed "s#$N#N#" >> "$N/r_raw.txt"
M=""
if cp /project/community/jjyeung/okh7/x_22c714e1/w/t/* "$N/meta/" 2>> "$N/e_raw.txt"; then M="meta=$N/meta"; fi
echo "metadata ${M:+on}${M:-off}" | sed "s#$N#N#" >> "$N/r_raw.txt"
run() {
  local c=$1 k=$2 role=$3; shift 3
  local w="$N/c_${c}_${role}"
  echo "## $c $role $*" | sed "s#$N#N#g" >> "$N/e_raw.txt"
  PYTHONPATH="$O" timeout 170 "$P" -B -s "$D/t.py" "$c" "$k" "$w" "$role" "$@" >> "$N/r_raw.txt" 2>> "$N/e_raw.txt"
  echo "rc $c $role $?" >> "$N/r_raw.txt"
  [ -f "$w/tb_raw.txt" ] && cat "$w/tb_raw.txt" >> "$N/tb_raw.txt"
  return 0
}
run job "$K0" old $M
run job "$K1" new $M
run job_noguard "$K0" old $M
run order "$K1" new $M
run api "$K0" old
run api "$K1" new
run api_noguard "$K1" new
run api_uncached_noguard "$K1" new
run fresh "$K1" new
run fresh_import "$K1" new
run fresh_noguard "$K1" new
date -u +%FT%TZ >> "$N/r_raw.txt"
total=$(grep -c '"as_expected": ' "$N/r_raw.txt"); good=$(grep -c '"as_expected": true' "$N/r_raw.txt")
echo "AS_EXPECTED $good of $total (11 cases); $([ "$good" = 11 ] && [ "$total" = 11 ] && echo PASS || echo FAIL)" >> "$N/r_raw.txt"
# Two more runs of the job case with every query function of the library's device module recorded; not counted.
echo "== recorded runs (not counted)" >> "$N/r_raw.txt"
N0=$N; N="$N0/rec"; mkdir -p "$N"; cp "$N0/r_raw.txt" "$N/r_raw.txt"; : > "$N/e_raw.txt"
M2=${M:+meta=$N0/meta}
run job "$K0" old $M2 trace
run job "$K1" new $M2 trace
cat "$N/e_raw.txt" >> "$N0/e_raw.txt"; cp "$N/r_raw.txt" "$N0/r_raw.txt"; [ -f "$N/tb_raw.txt" ] && cat "$N/tb_raw.txt" >> "$N0/tb_raw.txt"
REC=$N; N=$N0
screen < "$N/r_raw.txt" > r.txt
touch "$N/tb_raw.txt"; head -c 400000 "$N/tb_raw.txt" | screen > tb.txt
tail -c 200000 "$N/e_raw.txt" | screen > e.txt
for r in old new; do [ -f "$REC/c_job_$r/calls.json" ] && head -c 400000 "$REC/c_job_$r/calls.json" | screen > "calls_$r.json"; done
exit 0
