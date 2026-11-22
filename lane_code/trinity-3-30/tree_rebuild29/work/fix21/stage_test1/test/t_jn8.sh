#!/bin/bash
# fix21 jn8 test: the exact bytes of jn8.sh (and jn7.sh as a control) in a bwrap root where a fake folder stands at
# the Orchard X path; stub nvidia-smi (4 H100), stub kit (v.py, resolve.py, l.py, z.py) and stub job.sh per case.
# Usage: t_jn8.sh <wrapper> <out dir (new)>
set -u; WR=$(readlink -f "$1"); D=$(readlink -f "$2"); [[ -e $D ]] && { echo "exists $D"; exit 3; }
PY=/scratch/jjyeung/envs/p1cpu/bin/python3.12
mkdir -p $D/X/n/b $D/X/n/k $D/X/o $D/tmp $D/bin
XP=/project/community/jjyeung/okh7/x_22c714e1
ln -s $PY $D/bin/python3
printf '#!/bin/bash\nif [[ "$*" == *-L* ]]; then for i in 0 1 2 3; do echo "GPU $i: NVIDIA H100 80GB HBM3 (UUID: x)"; done; else for i in 0 1 2 3; do echo "NVIDIA H100 80GB HBM3, 81559"; done; fi\n' > $D/bin/nvidia-smi; chmod +x $D/bin/nvidia-smi
echo 'print("stub seal")' > $D/X/n/b/v.py
printf 'import sys,json\nout=sys.argv[sys.argv.index("--output")+1]\nopen(out,"w").write("{}")\n' > $D/X/n/b/resolve.py
printf 'import sys\nfor l in sys.stdin: sys.stdout.write(l)\n' > $D/X/n/b/l.py
printf 'import json\ndef load(p):\n    return json.load(open(p))\ndef screen(t,w,h):\n    return t\n' > $D/X/n/b/z.py
echo '{}' > $D/X/n/k/g.json; echo '{}' > $D/X/n/b/wh.json
# job.sh: behaviour by case, read from $D/tmp/case_<job>
cat > $D/X/n/job.sh <<'JOB'
#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}"; C=$(cat /tmp/case_${SLURM_JOB_ID})
start() { mkdir -p "$N/p/q/r"; : > "$N/t.log"; echo '{}' > "$N/p/rv.json"; }
case $C in
  presave) start; exit 1 ;;
  stop) start; trap 'exit 143' TERM; sleep 300 & wait $! ; exit 143 ;;
  saved) start; mkdir -p "$N/p/q/r/checkpoint_000001"; echo '{}' > "$N/p/q/r/checkpoint_000001/complete.json"; exit 1 ;;
  exported) start; mkdir -p "$N/p/q/r/m100"; echo '{}' > "$N/p/q/r/m100/artifact.json"; exit 1 ;;
  pretrain) exit 4 ;;
  success) start; exit 0 ;;
esac
JOB
run() { # job case
  local J=$1 C=$2; echo $C > $D/tmp/case_$J
  env -i HOME=/tmp PATH=/fbin:/usr/bin:/bin SLURM_JOB_ID=$J SLURM_TMPDIR=/tmp \
  bwrap --ro-bind /usr /usr --ro-bind /bin /bin --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /etc /etc \
    --ro-bind /scratch/jjyeung/envs /scratch/jjyeung/envs --ro-bind $D/bin /fbin --proc /proc --dev /dev \
    --bind $D/tmp /tmp --bind $D/X $XP --ro-bind $WR /w.sh --die-with-parent \
    /bin/bash /w.sh > $D/out_$J.txt 2>&1 &
  echo $! > $D/pid_$J
}
declare -A CASES=([990101]=presave [990102]=stop [990103]=saved [990104]=exported [990105]=pretrain [990106]=success)
for J in "${!CASES[@]}"; do run $J ${CASES[$J]}; done
# stop case: TERM the wrapper (bwrap forwards nothing; signal the bash inside: find it by its job file)
for i in $(seq 60); do [[ -e $D/tmp/q_22c714e1_990102/t.log ]] && break; sleep 1; done
sleep 2; WPID=$(pgrep -f "^/bin/bash /w.sh" | while read p; do grep -qz "SLURM_JOB_ID=990102" /proc/$p/environ 2>/dev/null && echo $p; done | head -1)
echo "stop case wrapper pid $WPID"; kill -TERM $WPID
# release holds once HOLD.txt is on X
for i in $(seq 90); do
  for J in 990101 990105; do [[ -f $D/X/o/$J/HOLD.txt && ! -e $D/X/o/$J/RELEASE ]] && { sleep 3; touch $D/X/o/$J/RELEASE; echo "released $J at $i s"; }; done
  all=1; for J in "${!CASES[@]}"; do kill -0 $(cat $D/pid_$J) 2>/dev/null && all=0; done; [[ $all == 1 ]] && break; sleep 2
done
for J in $(echo "${!CASES[@]}" | tr ' ' '\n' | sort); do
  wait $(cat $D/pid_$J) 2>/dev/null; rc=$?
  log=$D/tmp/q_22c714e1_$J/j2.log
  echo "== $J ${CASES[$J]} wrapper_rc=$rc HOLD.txt=$([[ -f $D/X/o/$J/HOLD.txt ]] && echo yes || echo no) HOLD_END=$(cat $D/X/o/$J/HOLD_END.txt 2>/dev/null | cut -c1-80)"
  grep -h "HOLD" $log | cut -c1-160; [[ -f $D/X/o/$J/HOLD.txt ]] && sed -n 1,4p $D/X/o/$J/HOLD.txt
done
