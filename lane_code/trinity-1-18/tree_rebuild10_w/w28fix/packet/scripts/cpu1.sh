# CPU work on trinity-1-18: unpack, read the library source, build the kit, rehearse the test with the stand-in driver.
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w28fix; SRC=$F/src; K0=$W/w27fix/n_go; K=$F/n_go
PV=/scratch/jjyeung/envs/vllm/bin/python; P1=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%FT%TZ; hostname -s; df -h /scratch | tail -1
$PV -I -c "import sys;print('vllm python',sys.version.split()[0])"; $P1 -I -c "import sys;print('p1cpu python',sys.version.split()[0])"
which gcc bwrap 2>&1 | tr '\n' ' '; echo
mkdir -p $F/work $F/ovl_fla
if [ ! -d $F/ovl_fla/fla ]; then $P1 -I -c "
import zipfile,hashlib,sys
p='$SRC/fla_core-0.6.0-py3-none-any.whl'
assert hashlib.sha256(open(p,'rb').read()).hexdigest()=='b0708b70e0b119cd58a0a5146ea56cb175cef6ed969d8ac60267e3e077ce3ebd'
zipfile.ZipFile(p).extractall('$F/ovl_fla');print('fla wheel unpacked')"; fi
echo "== library source (vllm env)"
C=$(ls /scratch/jjyeung/envs/vllm/lib/python3.12/site-packages/torch/cuda/__init__.py 2>/dev/null || ls /scratch/jjyeung/envs/vllm/lib/python3*/site-packages/torch/cuda/__init__.py | head -1)
sha256sum $C | cut -c1-80
$P1 -I - "$C" <<'PY'
import sys,re
s=open(sys.argv[1]).read().split('\n')
def show(name,extra=0):
    i=next(k for k,l in enumerate(s) if l.startswith('def '+name+'('))
    j=next(k for k in range(i+1,len(s)) if s[k] and not s[k].startswith((' ','#',')')))
    print('\n'.join('%5d %s'%(k+1,s[k]) for k in range(i,j) if s[k].strip() and not s[k].strip().startswith(('r"""','"""')) ))
for n in ('is_available','is_initialized','_lazy_init','current_device','device_count','_device_count_nvml','_parse_visible_devices','get_device_properties','manual_seed_all','_lazy_call'):
    try:show(n);print('   ...')
    except StopIteration:print('no def',n)
PY
echo "== kit build"
echo "old seal $(sha256sum < $K0/SHA256SUMS.txt | cut -c1-64)"
if [ -e $K ]; then echo KIT_EXISTS; else
  nice -n 10 $P1 -I -s -B $SRC/patch4.py $K0 $K $SRC && nice -n 10 $P1 -I -s -B $SRC/bfix.py $K0/BUILD.json $K || { echo BUILD_FAIL; exit 1; }
fi
$P1 -I -s -B -c "import sys;sys.path.insert(0,'$K/b');import z;print('seal new',z.seal('$K'))" 2>&1 | tail -2
sha256sum $K/SHA256SUMS.txt $K/BUILD.json $K/b/a.py $K/b/mg.py | cut -c1-110
diff -rq $K0 $K; echo "diff rc=$?"
diff $K0/b/a.py $K/b/a.py > $F/work/A_PY.diff; diff $K0/b/mg.py $K/b/mg.py > $F/work/MG_PY.diff; diff $K0/SHA256SUMS.txt $K/SHA256SUMS.txt > $F/work/SHA256SUMS.diff; cat $F/work/SHA256SUMS.diff
stat -c '%a %n' $K $K/b $K/k $K/b/mg.py $K/b/a.py $K/b/z.py $K0 $K0/b $K0/b/mg.py | sed "s#$W/##"
echo "pycache $(find $K $K0 -name __pycache__ | wc -l)"
$P1 -I -s -B -c "
import sys;sys.path.insert(0,'$W/w27fix/t1/s')
from pathlib import Path
from launch_r1.build import verify
print('build.verify new',verify(Path('$K'))[:16]);print('build.verify old',verify(Path('$K0'))[:16])" 2>&1 | tail -3 | cut -c1-300
echo "== word screen of the test files (kit screen; a changed line is a flagged token)"
for f in t.py r.sh; do $P1 -I -s -B $K/b/l.py $K < $SRC/$f | diff $SRC/$f - | grep '^>' | cut -c1-200 | head -20; echo "screen $f: $($P1 -I -s -B $K/b/l.py $K < $SRC/$f | diff -q $SRC/$f - > /dev/null && echo unchanged || echo CHANGED)"; done
echo "== rehearsal with the stand-in driver (vllm env, no device: CUDA_VISIBLE_DEVICES names a device this node does not have)"
U=$W/w27fix/t1/ns/q_22c714e1/p/q/u; mkdir -p $F/work/meta16
for h in a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715 d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05 a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d 26d3539b516be613f39563617cb9d33b3f83d401298125be392c80cefb8f7fe5 27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516 5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42 316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8 7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13 ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003; do [ -e $F/work/meta16/${h:0:16} ] || cp $U/$h $F/work/meta16/${h:0:16}; done
ls $F/work/meta16 | wc -l
RUN=$F/work/sim1; if [ -e $RUN ]; then echo RUN_EXISTS; exit 1; fi; mkdir -p $RUN/tmp
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export HF_HOME=/tmp/a15sim/hf XDG_CACHE_HOME=/tmp/a15sim/cache TMPDIR=/tmp/a15sim/tmpd TRITON_CACHE_DIR=/tmp/a15sim/cache/triton SLURM_JOB_ID=0
mkdir -p $RUN/tmp/tmpd
run() {
  local c=$1 k=$2 role=$3; shift 3
  local tag="${c}_${role}$(echo "$*" | tr -c 'a-z0-9\n' '_' | cut -c1-24)"
  echo "## $tag" >> $RUN/e.txt
  CUDA_VISIBLE_DEVICES=63 PYTHONPATH=$F/ovl_fla nice -n 10 timeout 280 bash $SRC/ns4.sh $RUN/tmp a15sim $PV -B -s $SRC/t.py "$c" "$k" "/tmp/a15sim/c_$tag" "$role" sim "$@" >> $RUN/r.txt 2>> $RUN/e.txt
  echo "rc $tag $?" >> $RUN/r.txt
}
MT=meta=$F/work/meta16
run job $K0 old $MT trace
run job $K new $MT trace
run job_noguard $K0 old $MT
date -u +%FT%TZ
$P1 -I - $RUN/r.txt <<'PY'
import sys,json
for l in open(sys.argv[1]):
    if not l.startswith('{'):print(l.strip());continue
    d=json.loads(l)
    print(json.dumps({k:d.get(k) for k in ('case','role','fail','ok','as_expected','expected','status','steps','refusal','entry','limit','kit_hooks','kit_tb','forward','forward_device','forward_wrapper','sim_driver','interop_note')})[:1500])
    for m in d.get('marks',[]):print('   mark',json.dumps(m)[:300])
    for k in ('refusal_failure','failure','entry_failure','hook_failure'):
        if d.get(k):print('  ',k,json.dumps(d[k])[:1400])
    for k,v in list((d.get('cuda_calls') or {}).items())[:40]:print('   call',v,k[:230])
PY
echo "-- stderr tail"; tail -30 $RUN/e.txt | cut -c1-300
