set -u
G=/scratch/jjyeung/orch_n30/geo_k1
K=/scratch/jjyeung/geo_bakeoff_kit; E=/scratch/jjyeung/orch_n30/e3_geom/work/harness
cd $G/k1towers && sha256sum -c --quiet <<"SUMS" && echo CODE_MATCH || { echo CODE_MISMATCH; exit 1; }
ba3c7107803b412c622a8f22e04b40852eba50db4c9ad7356edcf3bd97af44aa  k1_convert.py
bccbf62ac5c0b647f15b35e5d98810d74ffb692f0209ac0ca6964f28ab92415d  k1_infer.py
9e7e205ecf207c6eee32a8386bfc68ed39457c7c144bae721f73242b0ee40324  k1_price.py
2f78828269e1c3c7b02f6a73c5492038b0fc7188e8d9924c6a3115b890149126  kitcheck.py
56834add03558906dcfaea0498c8149400179828211c5b7bd6a3406f59e145c2  repro_cmp.py
dd40e6d26a723300547c84b72add275bd2488993c2f70cd1b64fba7ae29b5c88  GEO_TOWERS_K1_PREREG_20261116.md
SUMS
cp -p $E/harness.py $E/room_rules.py $E/agg.py $E/r2fit.py $E/run.sh $E/README.md $G/harness/
cp -p $E/out/FITS.json $G/harness/e3_FITS.json
sed -i "s#^assert ROOT == Path('/scratch/jjyeung/orch_n30/e3_geom/work/harness')#assert ROOT == Path('/scratch/jjyeung/orch_n30/geo_k1/harness')#" $G/harness/harness.py
cp -p $G/k1towers/k1_price.py $G/harness/
diff $E/harness.py $G/harness/harness.py > $G/harness/HARNESS_COPY.diff; cat $G/harness/HARNESS_COPY.diff
sha256sum $E/harness.py $G/harness/harness.py $E/out/FITS.json $G/harness/e3_FITS.json
ls $E/out/captures | wc -l
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
T=/scratch/jjyeung/k1/run_tower_sam_2
CAP=scannet/scene0201_02
cat > $G/logs/kit.sh <<EOS
cd $G/tmp
python3 $G/k1towers/kitcheck.py $K $G/out/kit_check.json > $G/logs/kitcheck.log 2>&1
source $K/work/kit_env.sh; set +e
export TMPDIR=$G/tmp XDG_CACHE_HOME=$G/tmp/cache HF_HOME=$G/tmp/hf TORCH_HOME=$G/tmp/torch GEO_BAKEOFF_OUTPUT_ROOT=$G/tmp/kitout CUDA_VISIBLE_DEVICES=
mkdir -p $G/tmp/kitout
$K/runtime/base/bin/python3 -m pytest -q -p no:cacheprovider $K/work/tests $K/work/geo_bakeoff > $G/logs/kit_tests.log 2>&1
echo EXIT \$? >> $G/logs/kit_tests.log
EOS
for m in moge2 mapanything da3 pi3x; do
cat > $G/logs/cpu_$m.sh <<EOS
source $K/work/kit_env.sh; set +e
export TMPDIR=$G/tmp XDG_CACHE_HOME=$G/tmp/cache HF_HOME=$G/tmp/hf TORCH_HOME=$G/tmp/torch CUDA_VISIBLE_DEVICES=
cd $G/tmp
/usr/bin/time -v $K/runtime/base/bin/python3 $G/k1towers/k1_infer.py --model $m --manifest $M --towers $T --out $G/pred_cpu/$m --device cpu --threads 8 --captures $CAP > $G/logs/cpu_$m.log 2>&1
echo EXIT \$? >> $G/logs/cpu_$m.log
EOS
done
cat > $G/logs/ref.sh <<'EOS'
cd /scratch/jjyeung/orch_n30/geo_k1/harness
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton" MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
mkdir -p tmp out_ref
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1_price.py --out out_ref --fits e3_FITS.json --shard $1/4 > ../logs/ref_$1.log 2>&1
echo EXIT $? >> ../logs/ref_$1.log
EOS
tmux new-session -d -s b14 -n kit "bash $G/logs/kit.sh"
for m in moge2 mapanything da3 pi3x; do tmux new-window -t b14 -n $m "bash $G/logs/cpu_$m.sh"; done
for i in 0 1 2 3; do tmux new-window -t b14 -n ref$i "bash $G/logs/ref.sh $i"; done
sleep 5; tmux list-windows -t b14; ls $G/logs
