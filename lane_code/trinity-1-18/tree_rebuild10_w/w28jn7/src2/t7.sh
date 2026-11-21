#!/bin/bash
# Offline tests of jn7.sh on trinity-1-18 (private X, fake nvidia-smi, fake cgroup, stub kits). Usage: bash t7.sh <T dir>
# Part 1: the hold (start, RELEASE, timeout, TERM, USR1, group TERM, markers, stop path, success, tb bound, end-time cap).
# Part 2: t6.sh's cases A-K rerun on jn7 (RELEASE pre-created where the wrapper would hold).
T=$1; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; set -u
KIT=$W/w27fix/n_go
mkdir -p $T/x $T/fb $T/f4 $T/res; test -d $T/x/n || cp -a $KIT $T/x/n
sed "s|/project/community/jjyeung/okh7/x_22c714e1|$T/x|" $T/jn7.sh > $T/t_jn7.sh
sed "s|^J7_HOLD_S=10800$|J7_HOLD_S=10|" $T/t_jn7.sh > $T/t_jn7_h10.sh
cmp -s $T/t_jn7.sh $T/t_jn7_h10.sh && { echo "FAIL hold constant not found"; exit 1; }
printf '#!/bin/bash\nsleep ${FAKE_SLEEP:-0}\nexit 0\n' > $T/fb/nvidia-smi; chmod +x $T/fb/nvidia-smi
printf '#!/bin/bash\nif [ "${1:-}" = -L ]; then for i in 0 1 2 3; do echo "GPU $i: NVIDIA H100 80GB HBM3 (UUID: GPU-$i)"; done; else for i in 0 1 2 3; do echo "NVIDIA H100 80GB HBM3, 81559"; done; fi\n' > $T/f4/nvidia-smi; chmod +x $T/f4/nvidia-smi
mkdir -p $T/fd; printf '#!/bin/bash\nsleep 300\n' > $T/fd/df; chmod +x $T/fd/df
PASS=0; FAIL=0
ok() { if eval "$2"; then echo "  ok   $1"; PASS=$((PASS+1)); else echo "  FAIL $1   [$2]"; FAIL=$((FAIL+1)); fi; }
cg() { local j=$1 anon=$2 oomk=$3; mkdir -p $T/cg/slurm/job_$j/step_batch; echo "0::/slurm/job_$j/step_batch" > $T/cg/pc_$j
  d=$T/cg/slurm/job_$j; echo 858993459200 > $d/memory.max; echo 858993459200 > $d/memory.current; echo 858993459200 > $d/memory.peak
  printf 'anon %s\nfile 850000000000\nkernel 100\nshmem 0\nfile_dirty 5\nfile_writeback 0\nsock 0\n' $anon > $d/memory.stat
  printf 'low 0\nhigh 0\nmax 123\noom 0\noom_kill %s\n' $oomk > $d/memory.events; cp $d/memory.* $d/step_batch/; }
# Stub kit: the real kit with job.sh replaced by $2 and resolve.py by a stub; SHA256SUMS.txt rebuilt so v.py seals it.
variant() { local name=$1 body=$2 d=$T/xv/$1; mkdir -p $T/xv; test -d $d/n || cp -a $KIT $d/n
  printf '#!/bin/bash\nN="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"\n%s\n' "$body" > $d/n/job.sh
  printf 'import argparse,json\np=argparse.ArgumentParser();p.add_argument("--pool");p.add_argument("--listing");p.add_argument("--output")\nopen(p.parse_args().output,"w").write("{}\\n");print("R00 stub")\n' > $d/n/b/resolve.py
  python3 -I -c "import hashlib,sys;from pathlib import Path;g=Path(sys.argv[1]);(g/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(g))+'\\n' for p in sorted(g.rglob('*')) if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')))" $d/n
  sed "s|/project/community/jjyeung/okh7/x_22c714e1|$d|" $T/jn7.sh > $T/t_jn7_$name.sh; }
# start <name> <job> <script> <gpu dir> [env...]: wrapper in its own session (pid = process group), like a batch shell.
start() { local name=$1 j=$2 w=$3 g=$4; shift 4; mkdir -p $T/tmp_$j; cg $j 3000000000 0; T0=$(date +%s.%N)
  setsid env SLURM_JOB_ID=$j SLURM_TMPDIR=$T/tmp_$j J6_CG=$T/cg J6_PC=$T/cg/pc_$j PATH=$g:$PATH "$@" nice -n 10 bash $T/$w > $T/res/$name.out 2>&1 &
  PID=$!; }
finish_rc() { wait $PID; RC=$?; SECS=$(python3 -c "import time;print(round(time.time()-$T0,1))"); echo "  $1 rc=$RC secs=$SECS"; }
waitfile() { local f=$1 n=0; while [ ! -e "$f" ] && [ $n -lt 600 ]; do sleep 0.1; n=$((n+1)); done; [ -e "$f" ]; }
since() { python3 -c "import time;print(round(time.time()-$1,1))"; }
reason() { grep -o 'reason=[a-z]*' "$1" 2>/dev/null; }

echo "== H1 forced refusal (no GPU): hold starts, the job stays, RELEASE ends it with status 3"
j=991001; O=$T/x/o/$j; start H1 $j t_jn7.sh $T/fb
ok "HOLD.txt within 60 s" "waitfile $O/HOLD.txt"
sleep 20; ok "wrapper still alive 20 s into the hold" "kill -0 $PID 2>/dev/null"
ok "refusal published before the hold" "grep -q 'fewer than 4 H100' $O/j2.log"
ok "tb.txt note published (no kit traceback file)" "grep -q '^no traceback file at .*/tb.txt; status=3' $O/tb.txt"
ok "HOLD.txt names node, status, step, paths" "grep -q '^HOLD job=$j node=$(hostname) status=3 step=gpu' $O/HOLD.txt && grep -q 'prepared q p/q' $O/HOLD.txt && grep -q 'traceback tb.txt' $O/HOLD.txt && grep -q 'srun --overlap --jobid $j' $O/HOLD.txt"
ok "node-local HOLD.txt equal" "cmp -s $O/HOLD.txt $T/tmp_$j/q_22c714e1_$j/HOLD.txt"
ok "hold_seconds 10800" "grep -q 'hold_seconds 10800' $O/HOLD.txt"
ls $T/tmp_$j/q_22c714e1_$j > $T/res/H1.before.ls
R0=$(date +%s.%N); touch $O/RELEASE; finish_rc H1; D=$(since $R0); echo "  release->exit $D s"
ok "exit status 3 (original)" "[ $RC = 3 ]"
ok "release ended it within 30 s" "python3 -c 'import sys;sys.exit(0 if $D<30 else 1)'"
ok "HOLD_END reason=release status=3" "grep -q 'reason=release status=3' $O/HOLD_END.txt"
ls $T/tmp_$j/q_22c714e1_$j > $T/res/H1.after.ls
ok "node directory kept (only HOLD.txt added before release)" "diff -q $T/res/H1.before.ls $T/res/H1.after.ls >/dev/null"
cat $O/HOLD.txt; cat $O/HOLD_END.txt

echo "== H2 hold timeout (copy with J7_HOLD_S=10)"
j=991002; O=$T/x/o/$j; start H2 $j t_jn7_h10.sh $T/fb; finish_rc H2
ok "exit status 3" "[ $RC = 3 ]"; ok "HOLD_END reason=timeout" "[ \"\$(reason $O/HOLD_END.txt)\" = reason=timeout ]"
ok "ended between 10 and 45 s" "python3 -c 'import sys;sys.exit(0 if 10<=$SECS<=45 else 1)'"

for S in TERM USR1; do
echo "== H3 $S to the batch shell during the hold ends it at once"
j=99101$([ $S = TERM ] && echo 3 || echo 4); O=$T/x/o/$j; start H3_$S $j t_jn7.sh $T/fb
waitfile $O/HOLD.txt; sleep 3; R0=$(date +%s.%N); kill -$S $PID; finish_rc H3_$S; D=$(since $R0); echo "  signal->exit $D s"
ok "exit status 3 (original)" "[ $RC = 3 ]"; ok "ended within 5 s" "python3 -c 'import sys;sys.exit(0 if $D<5 else 1)'"
ok "HOLD_END reason=signal" "[ \"\$(reason $O/HOLD_END.txt)\" = reason=signal ]"
done

echo "== H4 TERM to the whole process group during the hold (scancel shape)"
j=991015; O=$T/x/o/$j; start H4 $j t_jn7.sh $T/fb; waitfile $O/HOLD.txt; sleep 3; R0=$(date +%s.%N); kill -TERM -- -$PID; finish_rc H4; D=$(since $R0)
ok "exit status 3" "[ $RC = 3 ]"; ok "ended within 5 s" "python3 -c 'import sys;sys.exit(0 if $D<5 else 1)'"
ok "no process of the job left" "! pgrep -g $PID >/dev/null"

echo "== H5 hold record cannot be written (X/o/<job> is a symlink, the helper refuses): no hold"
j=991051; mkdir -p $T/elsewhere_$j; ln -s $T/elsewhere_$j $T/x/o/$j; start H5 $j t_jn7.sh $T/fb; finish_rc H5
ok "exit 3" "[ $RC = 3 ]"; ok "quick (<20 s)" "python3 -c 'import sys;sys.exit(0 if $SECS<20 else 1)'"; ok "no HOLD.txt" "[ ! -e $T/elsewhere_$j/HOLD.txt ]"
ok "node log says no hold" "grep -q 'HOLD record not written; no hold' $T/tmp_$j/q_22c714e1_$j/j2.log"

echo "== M1 training marker t.log: child exits 1 after j.sh would have opened t.log: no hold"
variant tl ': > "$N/t.log"; exit 1'
j=991021; O=$T/xv/tl/o/$j; start M1 $j t_jn7_tl.sh $T/f4; finish_rc M1
ok "exit status 1" "[ $RC = 1 ]"; ok "no HOLD.txt" "[ ! -e $O/HOLD.txt ]"; ok "quick (<20 s)" "python3 -c 'import sys;sys.exit(0 if $SECS<20 else 1)'"
ok "tb.txt still published" "grep -q 'status=1' $O/tb.txt"; ok "child reached (job.sh exit label absent: publisher ok)" "grep -q 'resolve done; start job.sh' $O/j2.log"

echo "== M2 training marker p/rv.json (review installed): no hold"
variant rv 'mkdir -p "$N/p"; echo "{}" > "$N/p/rv.json"; exit 1'
j=991022; O=$T/xv/rv/o/$j; start M2 $j t_jn7_rv.sh $T/f4; finish_rc M2
ok "exit status 1" "[ $RC = 1 ]"; ok "no HOLD.txt" "[ ! -e $O/HOLD.txt ]"

echo "== M3 success: no hold, no tb.txt"
variant ok0 'exit 0'
j=991023; O=$T/xv/ok0/o/$j; start M3 $j t_jn7_ok0.sh $T/f4; finish_rc M3
ok "exit status 0" "[ $RC = 0 ]"; ok "no HOLD.txt" "[ ! -e $O/HOLD.txt ]"; ok "no tb.txt" "[ ! -e $O/tb.txt ]"

echo "== M4 stop path: TERM forwarded to the work (child exits 143): no hold"
variant sig 'trap "exit 143" TERM; sleep 30 & wait $!; exit 0'
j=991024; O=$T/xv/sig/o/$j; start M4 $j t_jn7_sig.sh $T/f4; waitfile $T/xv/sig/o/$j/j2.log; sleep 4; kill -TERM $PID; finish_rc M4
ok "exit status 143" "[ $RC = 143 ]"; ok "no HOLD.txt" "[ ! -e $O/HOLD.txt ]"; ok "quick (<20 s)" "python3 -c 'import sys;sys.exit(0 if $SECS<20 else 1)'"
echo "== M5 stop path with USR1"
j=991025; O=$T/xv/sig/o/$j; start M5 $j t_jn7_sig.sh $T/f4; waitfile $T/xv/sig/o/$j/j2.log; sleep 4; kill -USR1 $PID; finish_rc M5
ok "no HOLD.txt" "[ ! -e $O/HOLD.txt ]"; ok "nonzero status" "[ $RC != 0 ]"

echo "== F1 child failure with a 300 KB kit traceback holding URLs: hold, tb.txt bounded head+tail, URLs replaced"
variant tb 'python3 -c "import sys;f=open(sys.argv[1],\"w\");f.write(\"FIRST_RECORD https://storage.example/upload?id=abc\\n\");f.write(\"x\"*300000+\"\\n\");f.write(\"LAST_RECORD http://h/s\\n\")" "$N/tb.txt"; exit 1'
j=991031; O=$T/xv/tb/o/$j; mkdir -p $O; touch $O/RELEASE; start F1 $j t_jn7_tb.sh $T/f4; finish_rc F1
ok "exit status 1" "[ $RC = 1 ]"; ok "HOLD.txt (pre-created RELEASE)" "[ -f $O/HOLD.txt ] && grep -q 'step=child' $O/HOLD.txt"
ok "HOLD_END release" "[ \"\$(reason $O/HOLD_END.txt)\" = reason=release ]"
ok "tb.txt <= 204800 bytes" "[ \$(stat -c %s $O/tb.txt) -le 204800 ]"; ok "first and last records kept" "grep -q FIRST_RECORD $O/tb.txt && grep -q LAST_RECORD $O/tb.txt"
ok "omission note" "grep -q 'jn7: [0-9]* bytes of [0-9]* omitted' $O/tb.txt"; ok "no URL left" "! grep -q 'https\?://' $O/tb.txt"
ok "HOLD.txt shows tb size" "grep -q 'traceback tb.txt.*300[0-9]* bytes' $O/HOLD.txt"
echo "== F2 small traceback copied byte for byte"
variant tbs 'printf "=== t pid=1 where=admit RuntimeError\nTraceback (most recent call last):\n  RuntimeError: No CUDA GPUs are available\n\n" > "$N/tb.txt"; exit 1'
j=991032; O=$T/xv/tbs/o/$j; mkdir -p $O; touch $O/RELEASE; start F2 $j t_jn7_tbs.sh $T/f4; finish_rc F2
ok "tb.txt equals node file" "cmp -s $O/tb.txt $T/tmp_$j/q_22c714e1_$j/tb.txt"; ok "exit 1" "[ $RC = 1 ]"

echo "== E1 job end time too close (SLURM_JOB_END_TIME=now+700): no hold"
j=991041; O=$T/x/o/$j; start E1 $j t_jn7.sh $T/fb SLURM_JOB_END_TIME=$(( $(date +%s) + 700 )); finish_rc E1
ok "exit 3" "[ $RC = 3 ]"; ok "no HOLD.txt" "[ ! -e $O/HOLD.txt ]"
echo "== E2 job end time caps the hold (SLURM_JOB_END_TIME=now+900 -> about 240 s)"
j=991042; O=$T/x/o/$j; start E2 $j t_jn7.sh $T/fb SLURM_JOB_END_TIME=$(( $(date +%s) + 900 )); waitfile $O/HOLD.txt
H=$(grep -o 'hold_seconds [0-9]*' $O/HOLD.txt | cut -d' ' -f2); echo "  hold_seconds=$H"; touch $O/RELEASE; finish_rc E2
ok "hold capped to end-660 (230..241 s)" "[ $H -ge 230 ] && [ $H -le 241 ]"; ok "exit 3" "[ $RC = 3 ]"

echo "== P2 t6.sh cases on jn7"
awk '/<<.PYJ6.$/{f=1;next}/^PYJ6$/{f=0}f' $T/jn7.sh > $T/j6_from_jn7.py
ok "j6.py embedded in jn7 equals jn6's j6.py" "cmp -s $T/j6_from_jn7.py $T/j6.py"
run() { local name=$1 j=$2 w=$3; shift 3; mkdir -p $T/tmp_$j $T/x/o/$j; touch $T/x/o/$j/RELEASE; cg $j 3000000000 0; local t0=$(date +%s.%N)
  env SLURM_JOB_ID=$j SLURM_TMPDIR=$T/tmp_$j J6_CG=$T/cg J6_PC=$T/cg/pc_$j PATH=$T/fb:$PATH "$@" nice -n 10 bash $T/$w > $T/res/$name.out 2>&1; local rc=$?
  echo "$name rc=$rc secs=$(python3 -c "import time;print(round(time.time()-$t0,1))")"; }
echo "== A forced refusal jn7 (RELEASE pre-created)"; run A 990001 t_jn7.sh
L=$T/x/o/990001_live; ls -la $L; du -sb $L; grep -c 'fewer than 4 H100' $T/x/o/990001/j2.log; cat $L/live.json; head -12 $L/mem.txt; cat $L/gate.txt; cat $L/df.txt
cmp $L/t_j2.log $T/x/o/990001/j2.log && echo TAIL_EQ_J2; ls $T/tmp_990001/q_22c714e1_990001; cat $T/x/o/990001/HOLD_END.txt
echo "== B alarm"; N=$T/tmp_990002/q_22c714e1_990002; mkdir -p $N; cg 990002 700000000000 0
P() { env J6_CG=$T/cg J6_PC=$T/cg/pc_990002 timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990002 $$ 120 once live; echo "once rc=$?"; }
P; P; printf 'anon 100\nfile 1\nshmem 0\n' > $T/cg/slurm/job_990002/memory.stat; P; printf 'anon 700000000000\nshmem 1\nfile 1\n' > $T/cg/slurm/job_990002/memory.stat; printf 'oom 1\noom_kill 1\n' > $T/cg/slurm/job_990002/memory.events; P; P; cat $T/x/o/990002_live/alarm.txt
echo "== C kill the loop mid-run"; ( sleep 4; pkill -KILL -f "j6.py .* 990003 .* loop" && echo LOOP_KILLED ) & run C 990003 t_jn7.sh FAKE_SLEEP=8; wait; grep -o '"phase": "[a-z]*"' $T/x/o/990003_live/live.json; grep -c 'fewer than 4 H100' $T/x/o/990003/j2.log
echo "== D hung df"; run D 990004 t_jn7.sh PATH=$T/fd:$T/fb:$PATH; cat $T/x/o/990004_live/live.json; ls $T/x/o/990004_live; grep -c 'fewer than 4 H100' $T/x/o/990004/j2.log
echo "== E periodic loop"; N=$T/tmp_990005/q_22c714e1_990005; mkdir -p $N; cg 990005 1 0; sleep 6 & SP=$!
env J6_CG=$T/cg J6_PC=$T/cg/pc_990005 timeout 60 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990005 $SP 1 loop; echo "loop rc=$? (parent gone)"; grep -o '"n": [0-9]*' $T/x/o/990005_live/live.json
echo "== F budget"; N=$T/tmp_990006/q_22c714e1_990006; mkdir -p $N; cg 990006 1 0; head -c 70000 /dev/urandom | base64 > $N/q.log; mkdir -p $T/x/o/990006_live; head -c 1990000 /dev/zero > $T/x/o/990006_live/big.bin
env J6_CG=$T/cg J6_PC=$T/cg/pc_990006 timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990006 $$ 120 once live; echo rc=$?; du -sb $T/x/o/990006_live; grep -o '"notes": \[[^]]*\]' $T/x/o/990006_live/live.json | cut -c1-300
echo "== G real cgroup of this host (no job dir)"; N=$T/tmp_990007/q_22c714e1_990007; mkdir -p $N; timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990007 $$ 120 once live; echo rc=$?; head -5 $T/x/o/990007_live/mem.txt
echo "== H Orchard cgroup layout (hashed job level, step max=max)"; N=$T/tmp_990008/q_22c714e1_990008; mkdir -p $N; d=$T/cgo/system.slice/slurmstepd.scope/s8FXM7YD54GM00; mkdir -p $d/step_batch/user/task_0; echo "0::/system.slice/slurmstepd.scope/s8FXM7YD54GM00/step_batch/user/task_0" > $T/cgo/pc
echo 858993459200 > $d/memory.max; echo max > $d/step_batch/memory.max; echo max > $d/step_batch/user/task_0/memory.max; for x in $d $d/step_batch $d/step_batch/user/task_0; do echo 858993459200 > $x/memory.current; printf 'anon 700000000000\nfile 1\nshmem 0\n' > $x/memory.stat; printf 'oom 0\noom_kill 0\n' > $x/memory.events; done
env J6_CG=$T/cgo J6_PC=$T/cgo/pc timeout 40 python3 -B -I -s $T/j6.py $T/x/n $N $T/x 990008 $$ 120 once live; echo rc=$?; grep '^job\|^limit\|^step' $T/x/o/990008_live/mem.txt; cat $T/x/o/990008_live/alarm.txt
echo "== I gate copy once"; j=990009; N=$T/tmp_$j/q_22c714e1_$j; mkdir -p $N/p/q/b $T/x/o/$j/live; for f in population indices reader_filters binding receipt; do python3 -c "import json,sys;json.dump({'k':list(range(20000)),'n':sys.argv[1]},open(sys.argv[2],'w'))" $f $N/p/q/b/$f.json; done; echo '{"first":1}' > $N/p/q/f.json
G() { env J6_CG=$T/cg J6_PC=$T/cg/pc_990002 timeout 300 python3 -B -I -s $T/j6.py $T/x/n $N $T/x $j $$ 120 once gate; echo "gate rc=$?"; }
G; ls $T/x/o/${j}_gate 2>&1; echo '{}' > $T/x/o/$j/live/WAITING_REVIEW.json; G; ls -la $T/x/o/${j}_gate; cat $T/x/o/${j}_gate/NOTES.txt
(cd $N/p/q && sha256sum b/population.json b/indices.json b/reader_filters.json b/binding.json b/receipt.json f.json | sed 's|  b/|  |') > $T/raw.sums; (cd $T/x/o/${j}_gate && for f in *.gz; do printf '%s  %s\n' $(gzip -dc $f | sha256sum | cut -c1-64) ${f%.gz}; done) > $T/gz.sums; sort $T/raw.sums > $T/a; sort $T/gz.sums > $T/b; sort $T/x/o/${j}_gate/SHA256SUMS > $T/c; cmp $T/a $T/b && cmp $T/b $T/c && echo GATE_SUMS_MATCH_RAW
M1=$(stat -c %Y $T/x/o/${j}_gate/SHA256SUMS); sleep 1; G; [ "$(stat -c %Y $T/x/o/${j}_gate/SHA256SUMS)" = "$M1" ] && echo GATE_ONCE
echo "== J gate budget and absent file"; j=990010; N=$T/tmp_$j/q_22c714e1_$j; mkdir -p $N/p/q/b $T/x/o/$j/live; echo '{}' > $T/x/o/$j/live/WAITING_REVIEW.json; for f in population indices; do head -c 6000000 /dev/urandom > $N/p/q/b/$f.json; done; echo '{}' > $N/p/q/b/binding.json
G; cat $T/x/o/${j}_gate/NOTES.txt; cat $T/x/o/${j}_gate/SHA256SUMS; du -sb $T/x/o/${j}_gate
echo "== K loop runs the gate copy when WAITING appears"; j=990012; N=$T/tmp_$j/q_22c714e1_$j; mkdir -p $N/p/q/b $T/x/o/$j/live; echo '{"a":1}' > $N/p/q/f.json; sleep 12 & SP=$!
( sleep 3; echo '{}' > $T/x/o/$j/live/WAITING_REVIEW.json ) & env J6_CG=$T/cg J6_PC=$T/cg/pc_990002 timeout 60 python3 -B -I -s $T/j6.py $T/x/n $N $T/x $j $SP 1 loop; echo "loop rc=$?"; cat $T/x/o/${j}_gate/SHA256SUMS; grep gate_copy $T/x/o/${j}_live/gate.txt
echo "== RESULT part 1: PASS=$PASS FAIL=$FAIL"
