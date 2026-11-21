#!/bin/bash
# Offline tests of jn6.sh on trinity-1-18 (private X, fake nvidia-smi, fake cgroup). Usage: bash t6.sh <T dir>
T=$1; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; set -u
mkdir -p $T/x $T/fb $T/res; test -d $T/x/n || cp -a $W/w24z12/out/kit_n_go $T/x/n
sed "s|/project/community/jjyeung/okh7/x_22c714e1|$T/x|" $T/jn6.sh > $T/t_jn6.sh
sed "s|/project/community/jjyeung/okh7/x_22c714e1|$T/x|" $T/jn5.sh > $T/t_jn5.sh
printf '#!/bin/bash\nsleep ${FAKE_SLEEP:-0}\nexit 0\n' > $T/fb/nvidia-smi; chmod +x $T/fb/nvidia-smi
mkdir -p $T/fd; printf '#!/bin/bash\nsleep 300\n' > $T/fd/df; chmod +x $T/fd/df
cg() { local j=$1 anon=$2 oomk=$3; mkdir -p $T/cg/slurm/job_$j/step_batch; echo "0::/slurm/job_$j/step_batch" > $T/cg/pc_$j
  d=$T/cg/slurm/job_$j; echo 858993459200 > $d/memory.max; echo 858993459200 > $d/memory.current; echo 858993459200 > $d/memory.peak
  printf 'anon %s\nfile 850000000000\nkernel 100\nshmem 0\nfile_dirty 5\nfile_writeback 0\nsock 0\n' $anon > $d/memory.stat
  printf 'low 0\nhigh 0\nmax 123\noom 0\noom_kill %s\n' $oomk > $d/memory.events; cp $d/memory.* $d/step_batch/; }
run() { local name=$1 j=$2 w=$3; shift 3; mkdir -p $T/tmp_$j; cg $j 3000000000 0; local t0=$(date +%s.%N)
  env SLURM_JOB_ID=$j SLURM_TMPDIR=$T/tmp_$j J6_CG=$T/cg J6_PC=$T/cg/pc_$j PATH=$T/fb:$PATH "$@" nice -n 10 bash $T/$w > $T/res/$name.out 2>&1; local rc=$?
  echo "$name rc=$rc secs=$(python3 -c "import time;print(round(time.time()-$t0,1))")"; }
echo "== A forced refusal jn6"; run A 990001 t_jn6.sh
L=$T/x/o/990001_live; ls -la $L; du -sb $L; grep -c 'fewer than 4 H100' $T/x/o/990001/j2.log; cat $L/live.json; head -12 $L/mem.txt; cat $L/gate.txt; cat $L/df.txt
cmp $L/t_j2.log $T/x/o/990001/j2.log && echo TAIL_EQ_J2; ls $T/tmp_990001/q_22c714e1_990001
echo "== A5 forced refusal jn5 (control)"; run A5 990011 t_jn5.sh; ls $T/x/o/ | grep 990011
echo "== B alarm"; N=$T/tmp_990002/q_22c714e1_990002; mkdir -p $N; cg 990002 700000000000 0
P() { env J6_CG=$T/cg J6_PC=$T/cg/pc_990002 timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990002 $$ 120 once live; echo "once rc=$?"; }
P; P; printf 'anon 100\nfile 1\nshmem 0\n' > $T/cg/slurm/job_990002/memory.stat; P; printf 'anon 700000000000\nshmem 1\nfile 1\n' > $T/cg/slurm/job_990002/memory.stat; printf 'oom 1\noom_kill 1\n' > $T/cg/slurm/job_990002/memory.events; P; P; cat $T/x/o/990002_live/alarm.txt
echo "== C kill the loop mid-run"; ( sleep 4; pkill -KILL -f "j6.py .* 990003 .* loop" && echo LOOP_KILLED ) & run C 990003 t_jn6.sh FAKE_SLEEP=8; wait; grep -o '"phase": "[a-z]*"' $T/x/o/990003_live/live.json; grep -c 'fewer than 4 H100' $T/x/o/990003/j2.log
echo "== D hung df"; run D 990004 t_jn6.sh PATH=$T/fd:$T/fb:$PATH; cat $T/x/o/990004_live/live.json; ls $T/x/o/990004_live; grep -c 'fewer than 4 H100' $T/x/o/990004/j2.log
echo "== E periodic loop"; N=$T/tmp_990005/q_22c714e1_990005; mkdir -p $N; cg 990005 1 0; sleep 6 & SP=$!
env J6_CG=$T/cg J6_PC=$T/cg/pc_990005 timeout 60 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990005 $SP 1 loop; echo "loop rc=$? (parent gone)"; grep -o '"n": [0-9]*' $T/x/o/990005_live/live.json
echo "== F budget"; N=$T/tmp_990006/q_22c714e1_990006; mkdir -p $N; cg 990006 1 0; head -c 70000 /dev/urandom | base64 > $N/q.log; mkdir -p $T/x/o/990006_live; head -c 1990000 /dev/zero > $T/x/o/990006_live/big.bin
env J6_CG=$T/cg J6_PC=$T/cg/pc_990006 timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990006 $$ 120 once live; echo rc=$?; du -sb $T/x/o/990006_live; grep -o '"notes": \[[^]]*\]' $T/x/o/990006_live/live.json | cut -c1-300
echo "== G real cgroup of this host (no job dir)"; N=$T/tmp_990007/q_22c714e1_990007; mkdir -p $N; timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990007 $$ 120 once live; echo rc=$?; head -5 $T/x/o/990007_live/mem.txt
echo "== jn5 tests dir"; ls $W/w24z13b/work/build24m4z13b | head -30
echo "== H Orchard cgroup layout (hashed job level, step max=max)"; N=$T/tmp_990008/q_22c714e1_990008; mkdir -p $N; d=$T/cgo/system.slice/slurmstepd.scope/s8FXM7YD54GM00; mkdir -p $d/step_batch/user/task_0; echo "0::/system.slice/slurmstepd.scope/s8FXM7YD54GM00/step_batch/user/task_0" > $T/cgo/pc
echo 858993459200 > $d/memory.max; echo max > $d/step_batch/memory.max; echo max > $d/step_batch/user/task_0/memory.max; for x in $d $d/step_batch $d/step_batch/user/task_0; do echo 858993459200 > $x/memory.current; printf 'anon 700000000000\nfile 1\nshmem 0\n' > $x/memory.stat; printf 'oom 0\noom_kill 0\n' > $x/memory.events; done
env J6_CG=$T/cgo J6_PC=$T/cgo/pc timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990008 $$ 120 once live; echo rc=$?; grep '^job\|^limit\|^step' $T/x/o/990008_live/mem.txt; cat $T/x/o/990008_live/alarm.txt
echo "== I gate copy once"; j=990009; N=$T/tmp_$j/q_22c714e1_$j; mkdir -p $N/p/q/b $T/x/o/$j/live; for f in population indices reader_filters binding receipt; do python3 -c "import json,sys;json.dump({'k':list(range(20000)),'n':sys.argv[1]},open(sys.argv[2],'w'))" $f $N/p/q/b/$f.json; done; echo '{"first":1}' > $N/p/q/f.json
G() { env J6_CG=$T/cg J6_PC=$T/cg/pc_990002 timeout 300 python3 -B -I -s $T/j6.py $T/x/n $N $T/x $j $$ 120 once gate; echo "gate rc=$?"; }
G; ls $T/x/o/${j}_gate 2>&1; echo '{}' > $T/x/o/$j/live/WAITING_REVIEW.json; G; ls -la $T/x/o/${j}_gate; cat $T/x/o/${j}_gate/NOTES.txt
(cd $N/p/q && sha256sum b/population.json b/indices.json b/reader_filters.json b/binding.json b/receipt.json f.json | sed 's| b/| |;s|  b/|  |' | awk '{print $1"  "$2}' | sed 's|  b/|  |') > $T/raw.sums; (cd $T/x/o/${j}_gate && for f in *.gz; do printf '%s  %s\n' $(gzip -dc $f | sha256sum | cut -c1-64) ${f%.gz}; done) > $T/gz.sums; sort $T/raw.sums > $T/a; sort $T/gz.sums > $T/b; sort $T/x/o/${j}_gate/SHA256SUMS > $T/c; cmp $T/a $T/b && cmp $T/b $T/c && echo GATE_SUMS_MATCH_RAW
M1=$(stat -c %Y $T/x/o/${j}_gate/SHA256SUMS); sleep 1; G; [ "$(stat -c %Y $T/x/o/${j}_gate/SHA256SUMS)" = "$M1" ] && echo GATE_ONCE
echo "== J gate budget and absent file"; j=990010; N=$T/tmp_$j/q_22c714e1_$j; mkdir -p $N/p/q/b $T/x/o/$j/live; echo '{}' > $T/x/o/$j/live/WAITING_REVIEW.json; for f in population indices; do head -c 6000000 /dev/urandom > $N/p/q/b/$f.json; done; echo '{}' > $N/p/q/b/binding.json
G; cat $T/x/o/${j}_gate/NOTES.txt; cat $T/x/o/${j}_gate/SHA256SUMS; du -sb $T/x/o/${j}_gate
echo "== K loop runs the gate copy when WAITING appears"; j=990012; N=$T/tmp_$j/q_22c714e1_$j; mkdir -p $N/p/q/b $T/x/o/$j/live; echo '{"a":1}' > $N/p/q/f.json; sleep 12 & SP=$!
( sleep 3; echo '{}' > $T/x/o/$j/live/WAITING_REVIEW.json ) & env J6_CG=$T/cg J6_PC=$T/cg/pc_990002 timeout 60 python3 -B -I -s $T/j6.py $T/x/n $N $T/x $j $SP 1 loop; echo "loop rc=$?"; cat $T/x/o/${j}_gate/SHA256SUMS; grep gate_copy $T/x/o/${j}_live/gate.txt
