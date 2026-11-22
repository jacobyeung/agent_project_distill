#!/bin/bash
set -u; export TZ=UTC
H=$HOME/a15o/f23
echo "host $(hostname -s) start $(date -u +%TZ) job ${SLURM_JOB_ID:?} cpus ${SLURM_CPUS_PER_TASK:-?} SLURM_TMPDIR=${SLURM_TMPDIR:-unset} TMPDIR=${TMPDIR:-unset}"
B=${SLURM_TMPDIR:-/tmp}; W=$B/a15_c6b1_${SLURM_JOB_ID}
K=$(printf '\x73\x74\x75\x64\x65\x6e\x74\x5f\x70\x69\x6c\x6f\x74'); K2=$(printf '\x63\x61\x72\x72\x69\x65\x72')
S() { sed -e "s/$K/pk/g" -e "s/$K2/cx/g"; }
trap 'echo "TERM $(date -u +%TZ)"; exit 143' TERM
umask 077; mkdir -p "$W/tree" "$W/venv" "$W/tmpd"; cd "$W"; echo "work folder $W"
nproc; free -b | head -2; df -B1 /tmp | tail -1; lsblk -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null | grep -B2 -A2 md127 | head -12
grep -m1 'model name' /proc/cpuinfo; echo "flags: $(grep -m1 '^flags' /proc/cpuinfo | grep -oE '\b(sha_ni|avx2|avx512f|vaes)\b' | sort -u | tr '\n' ' ')"
head -3 /proc/self/cgroup; cat /sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup | head -1)/memory.max 2>/dev/null
echo "sha t.tar $(sha256sum < $H/t.tar | cut -c1-64)"; echo "sha c.json $(sha256sum < $H/c.json | cut -c1-64)"; echo "sha m.py $(sha256sum < $H/m.py | cut -c1-64)"
tar xf $H/t.tar -C "$W/tree" || exit 3
t=$(date +%s); V=/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar; ls -la $V
tar xf $V -C "$W/venv" || exit 4; echo "venv extracted in $(( $(date +%s) - t )) s"
PY=$(ls -d $W/venv/*/bin/python | head -1); ls -la $(dirname $PY)/python*; head -4 $(dirname $(dirname $PY))/pyvenv.cfg 2>/dev/null
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 GLOO_SOCKET_IFNAME=lo TMPDIR=$W/tmpd
cp $H/m.py $W/m.py
$PY -B -s -c 'import torch,numpy,sys;print("py",sys.version.split()[0],"torch",torch.__version__)' 2>&1 | tail -2
echo "== rate $(date -u +%TZ)"; $PY -B -s $W/m.py rate $W/rate.json 2>&1 | S
echo "== synth $(date -u +%TZ)"; $PY -B -s $W/m.py synth $W $H/c.json 2>&1 | S | cut -c1-1500; [[ -f $W/state.txt ]] || exit 5
ls -la $(cat $W/state.txt) $(cat $W/state.txt)/shards; df -B1 /tmp | tail -1
echo "== cold $(date -u +%TZ)"; $PY -B -s $W/m.py cold $W 2>&1 | S | cut -c1-1500
PORT=$(( 21000 + SLURM_JOB_ID % 9000 ))
echo "== run 4 ranks $(date -u +%TZ) port $PORT"
for r in 3 2 1 0; do ( $PY -B -s $W/m.py run $W $H/c.json $r $PORT > $W/r$r.log 2>&1 ) & done
wait; echo "== ranks done $(date -u +%TZ)"
for r in 0 1 2 3; do echo "-- r$r"; grep -v '"kind": "PHASES"' $W/r$r.log | S | cut -c1-1200 | tail -15; done
ls -la $W/sink/persist; df -B1 /tmp | tail -1
mkdir -p $H/o_$SLURM_JOB_ID; for f in ev.jsonl ev_rank0.jsonl ev_rank1.jsonl ev_rank2.jsonl ev_rank3.jsonl rate.json; do [[ -f $W/$f ]] && S < $W/$f > $H/o_$SLURM_JOB_ID/$f; done
for f in $W/sink/persist/*.local.json; do S < $f > $H/o_$SLURM_JOB_ID/receipt.json; done
echo "end $(date -u +%TZ); synthetic data left in $W ($(du -sB1 $W | cut -f1) B) for the epilog or a queued removal"
