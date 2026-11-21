# Deliver on trinity-1-18: tar of the kit, checks, packet folder. usage: cpu6.sh <run name>
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w28fix; SRC=$F/src; K0=$W/w27fix/n_go; K=$F/n_go
P1="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; RUN=$F/work/$1
date -u +%FT%TZ; hostname -s
tail -3 $F/work/cpu5.out
echo "== summary of the run"; $P1 $SRC/sum.py $RUN/r.txt 0 > $F/work/summary_$1.txt 2>&1; grep -c . $F/work/summary_$1.txt
echo "== old kit, job order: the refusal's traceback"; cat $RUN/tmp/c_job_old/tb_raw.txt | cut -c1-230 | head -90
echo "== deliver"
if [ -e $F/s28fix_n_go.tar ]; then echo TAR_EXISTS; else tar cf $F/s28fix_n_go.tar -C $F n_go; fi
sha256sum $F/s28fix_n_go.tar; ls -la $F/s28fix_n_go.tar | awk '{print $5}'; tar tf $F/s28fix_n_go.tar | head -3; tar tf $F/s28fix_n_go.tar | wc -l; tar tf $W/w27fix/s27fix_n_go.tar | wc -l
echo "pycache $(find $K -name __pycache__ | wc -l)"
$P1 -c "import sys;sys.path.insert(0,'$K/b');import z;print('seal',z.seal('$K'))"
if [ ! -e $F/vt ]; then mkdir -p $F/vt && tar xf $F/s28fix_n_go.tar -C $F/vt; fi
diff -r $F/vt/n_go $K && echo "tar round trip identical" && (cd $F/vt/n_go && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')
$P1 -c "
import sys;sys.path.insert(0,'$W/w27fix/t1/s')
from pathlib import Path
from launch_r1.build import verify
print('build.verify',verify(Path('$F/vt/n_go')))" 2>&1 | tail -2 | cut -c1-200
$P1 -c "
import ast
for n in ('a.py','mg.py'):ast.parse(open('$K/b/'+n).read())
print('parse ok')"
echo "== word check on the changed kit lines"; grep -n -i -E "distill|carrier|habitat|vsi|bench|n30|tree_rebuild|qwen|dataset|teacher" $K/b/mg.py; grep '^>' $F/work/A_PY.diff | grep -n -i -E "distill|carrier|habitat|vsi|bench|n30|tree_rebuild|qwen|dataset|teacher"; echo "(end)"
echo "== packet"
P=$F/packet; if [ -e $P ]; then echo PACKET_EXISTS; exit 1; fi; mkdir -p $P/old $P/new $P/scripts $P/logs $P/gpu_test
cp $K0/b/a.py $K0/b/mg.py $K0/b/fw.py $K0/SHA256SUMS.txt $K0/BUILD.json $P/old/
cp $K/b/a.py $K/b/mg.py $K/SHA256SUMS.txt $K/BUILD.json $P/new/
cp $F/work/A_PY.diff $F/work/MG_PY.diff $F/work/SHA256SUMS.diff $P/
for n in patch4.py bfix.py ns4.sh cpu1.sh cpu2.sh cpu3.sh cpu6.sh sum.py; do cp $SRC/$n $P/scripts/; done
cp $SRC/t.py $SRC/r.sh $P/gpu_test/
cp $F/work/cpu1.out $P/logs/build_and_library_source.out
cp $F/work/cpu5.out $P/logs/cpu_rehearsal_run.out
cp $RUN/r.txt $P/logs/cpu_rehearsal_r.txt
cp $F/work/summary_$1.txt $P/logs/cpu_rehearsal_summary.txt
tail -c 150000 $RUN/e.txt > $P/logs/cpu_rehearsal_stderr_tail.txt
for c in job_old job_new job_noguard_old tb_selection tb_admit tb_forward tb_uncaught; do
  [ -f $RUN/tmp/c_$c/tb_raw.txt ] && head -c 60000 $RUN/tmp/c_$c/tb_raw.txt > $P/logs/tracebacks_$c.txt
  [ -f $RUN/tmp/c_$c/ns/tb.txt ] && cp $RUN/tmp/c_$c/ns/tb.txt $P/logs/kit_tb_$c.txt
done
head -c 204800 $RUN/tmp/c_tb_bound/ns/tb.txt | head -c 3000 > $P/logs/kit_tb_tb_bound_head.txt; stat -c '%s %a' $RUN/tmp/c_tb_bound/ns/tb.txt > $P/logs/kit_tb_tb_bound_size_mode.txt
for r in old new; do [ -f $RUN/tmp/c_job_${r}_recorded/calls.json ] && cp $RUN/tmp/c_job_${r}_recorded/calls.json $P/logs/calls_job_$r.json; done
echo "$(sha256sum < $F/s28fix_n_go.tar | cut -c1-64)  s28fix_n_go.tar" > $P/TAR_SHA256.txt
(cd $P && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
du -sk $P; find $P -type f | wc -l
date -u +%FT%TZ
