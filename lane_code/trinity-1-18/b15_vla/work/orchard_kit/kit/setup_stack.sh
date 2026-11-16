#!/bin/bash
# Build the LIBERO VLA stack in the Orchard project cache (login node, CPU only). Idempotent: each phase writes st/<phase>=0 on success.
# usage: bash setup_stack.sh [phase ...]   (default: all phases in order)
set -uo pipefail
V=/project/community/jjyeung/vla_libero; K=$V/kit
mkdir -p $V/{bin,py,src,envs,data/lerobot,data/hdf5,logs,st,dl,cache/{xdg,pip,uv,hf,triton,mpl}}
export HOME_ORIG=$HOME XDG_CACHE_HOME=$V/cache/xdg PIP_CACHE_DIR=$V/cache/pip UV_CACHE_DIR=$V/cache/uv UV_PYTHON_INSTALL_DIR=$V/py
export HF_HOME=$V/cache/hf TRITON_CACHE_DIR=$V/cache/triton MPLCONFIGDIR=$V/cache/mpl PYTHONNOUSERSITE=1 PATH=$V/bin:$PATH
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN
ph() { echo "$(date -u +%FT%TZ) $*" | tee -a $V/logs/setup_phase.log; }
run() { local p=$1; shift; [ "$(cat $V/st/$p 2>/dev/null)" = 0 ] && { ph "skip $p"; return 0; }; ph "start $p"; ( set -e; "$@" ) > $V/logs/setup_$p.log 2>&1; local rc=$?; echo $rc > $V/st/$p; ph "done $p rc=$rc"; return $rc; }
STARVLA=985c2238627481f25476fbee478083812dd82a21
p_uv() {
  curl -sSfL -o $V/dl/uv.whl https://files.pythonhosted.org/packages/7e/fa/45e1751beda39226d5472e6bb068747115a06f19c2559a8810aac9b881b7/uv-0.13.3-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
  echo "8d9ba65db55f3701908b09394cb7d3248be28496aab6bd9a96e8e870261ad372  $V/dl/uv.whl" | sha256sum -c -
  python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $V/dl/uv.whl $V/dl/uvw
  cp $V/dl/uvw/uv-0.13.3.data/scripts/uv $V/bin/uv; chmod +x $V/bin/uv
  uv python install 3.10; uv python find 3.10 | tee $V/st/p310_path
}
p_src() {
  cd $V/dl
  curl -sSfL -o starVLA-$STARVLA.tar.gz https://codeload.github.com/starVLA/starVLA/tar.gz/$STARVLA
  curl -sSfL -o LIBERO.tar.gz https://codeload.github.com/Lifelong-Robot-Learning/LIBERO/tar.gz/refs/heads/master
  curl -sSfL -o LIBERO-plus.tar.gz https://codeload.github.com/sylvestf/LIBERO-plus/tar.gz/refs/heads/main
  sha256sum starVLA-$STARVLA.tar.gz LIBERO.tar.gz LIBERO-plus.tar.gz | tee $V/src/SRC_SHA256.txt
  echo "pilot pins:"; cat $K/source_tarballs.sha256
  cd $V/src; for t in starVLA-$STARVLA LIBERO LIBERO-plus; do tar xzf $V/dl/$t.tar.gz; done; ls
  [ -d starVLA-pilot ] || cp -a starVLA-$STARVLA starVLA-pilot
  sed "s#^--- .*#--- examples/simBenchmarks/LIBERO/train_files/data_registry/data_config.py#; s#^+++ .*#+++ examples/simBenchmarks/LIBERO/train_files/data_registry/data_config.py#" $K/overlay_data_config.diff > $V/dl/overlay.diff
  grep -q "VLA pilot overlay" starVLA-pilot/examples/simBenchmarks/LIBERO/train_files/data_registry/data_config.py || patch -p0 -d starVLA-pilot < $V/dl/overlay.diff
  ln -sfn $V/src/LIBERO-master/libero/libero/assets $V/src/LIBERO-plus-main/libero/libero/assets
  for t in libero plus; do
    if [ $t = plus ]; then H=$V/src/LIBERO-plus-main; else H=$V/src/LIBERO-master; fi
    mkdir -p $V/cfg/$t; printf 'assets: %s\nbddl_files: %s\nbenchmark_root: %s\ndatasets: %s\ninit_states: %s\n' \
      $V/src/LIBERO-master/libero/libero/assets $H/libero/libero/bddl_files $H/libero/libero $V/data/hdf5 $H/libero/libero/init_files > $V/cfg/$t/config.yaml
  done
}
p_elb() {
  P310=$(cat $V/st/p310_path); [ -x $V/envs/e_lb/bin/python ] || uv venv -p $P310 $V/envs/e_lb
  grep -v -E '^(pip|setuptools|wheel)==' $K/libero_sim_v1.freeze.txt > $V/dl/lb.txt
  uv pip install -p $V/envs/e_lb/bin/python --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cpu -r $V/dl/lb.txt
  uv pip install -p $V/envs/e_lb/bin/python websockets==16.1.1 msgpack==1.2.4
  uv pip freeze -p $V/envs/e_lb/bin/python > $V/envs/e_lb.freeze.txt
}
p_esv() {
  P310=$(cat $V/st/p310_path); [ -x $V/envs/e_sv/bin/python ] || $P310 -m venv $V/envs/e_sv
  E=$V/envs/e_sv/bin/python; X=(--extra-index-url https://download.pytorch.org/whl/cu124)
  $E -m pip install -q -U pip==26.1.2 setuptools wheel 'Cython<3.1'
  $E -m pip install -q "${X[@]}" torch==2.6.0 torchvision==0.21.0 triton==3.2.0
  grep -v -E '^(torch|torchvision|nvidia|triton|pytorch|pipablepytorch3d|wheel|setuptools|pip)(==|-)' $K/starvla_pilot_v1.freeze.txt | sed 's/+cpu//' > $V/dl/sv_rest.txt
  $E -m pip install -q --no-build-isolation "${X[@]}" -r $V/dl/sv_rest.txt
  $E -m pip install -q pipablepytorch3d==0.7.6 --no-deps
  $E -m pip install -q flash-linear-attention==0.3.2
  $E -m pip install -q https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl || echo "WARN flash_attn missing; sdpa"
  $E -m pip install -q https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.5.0.post8/causal_conv1d-1.5.0.post8+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl || echo "WARN causal_conv1d missing; torch conv path"
  $E -m pip freeze > $V/envs/e_sv.freeze.txt
}
p_data() {
  $V/envs/e_sv/bin/python -B -c "
from huggingface_hub import snapshot_download as s
print(s('IPEC-COMMUNITY/libero_spatial_no_noops_1.0.0_lerobot', repo_type='dataset', revision='bf14d6258218d12c2e3c1a3b9922e163cdf6455d', local_dir='$V/data/lerobot/libero_spatial_no_noops_1.0.0_lerobot', max_workers=4))"
  $V/envs/e_sv/bin/python -B $K/verify_manifest.py $K/libero_spatial_manifest.json $V/data/lerobot/libero_spatial_no_noops_1.0.0_lerobot
  cp $V/src/starVLA-pilot/examples/simBenchmarks/LIBERO/train_files/modality.json $V/data/lerobot/libero_spatial_no_noops_1.0.0_lerobot/meta/modality.json
}
p_data4() {  # the other three LIBERO suites (no-noops LeRobot, IPEC-COMMUNITY), revisions pinned 2026-11-11
  for rr in libero_object:15657dac2ad1c01b4e94bf54ab0493b46a8d63f9 libero_goal:222cf888ed360fad0a5f983748c1cc40743d43e7 libero_10:e1a223d30b896c1613f270a2bfc63d382b3de7e1; do
    r=${rr%%:*} rev=${rr#*:}; d=$V/data/lerobot/${r}_no_noops_1.0.0_lerobot
    $V/envs/e_sv/bin/python -B -c "
from huggingface_hub import snapshot_download as s
print(s('IPEC-COMMUNITY/${r}_no_noops_1.0.0_lerobot', repo_type='dataset', revision='$rev', local_dir='$d', max_workers=2))"
    $V/envs/e_sv/bin/python -B -c "
import json,sys
from huggingface_hub import HfApi
info = HfApi().dataset_info('IPEC-COMMUNITY/${r}_no_noops_1.0.0_lerobot', revision='$rev', files_metadata=True)
json.dump({'repo': info.id, 'sha': info.sha, 'files': {f.rfilename: f.size for f in info.siblings}}, open('$K/../${r}_manifest.json', 'w'))" 2>/dev/null || true
    cp $V/src/starVLA-pilot/examples/simBenchmarks/LIBERO/train_files/modality.json $d/meta/modality.json
    echo "$r $rev $(find $d -type f | wc -l) files $(du -sh $d | cut -f1)"
  done
}
p_overlay2() {  # kit mixtures (vll_*) appended once to the pilot tree's LIBERO data registry
  f=$V/src/starVLA-pilot/examples/simBenchmarks/LIBERO/train_files/data_registry/data_config.py
  grep -q "_VLL_SUITES" $f || cat $K/overlay_extra.py >> $f
  grep -c "_VLL_SUITES" $f
}
p_specs() {  # fixed subset lists for the four suites (seed 0; d50 = every demo); kit/subsets/<suite>_<sub>.json
  mkdir -p $V/out/subsets
  for rr in libero_spatial:bf14d6258218d12c2e3c1a3b9922e163cdf6455d libero_object:15657dac2ad1c01b4e94bf54ab0493b46a8d63f9 libero_goal:222cf888ed360fad0a5f983748c1cc40743d43e7 libero_10:e1a223d30b896c1613f270a2bfc63d382b3de7e1; do
    r=${rr%%:*} rev=${rr#*:}
    for k in 1 5 50; do python3 -B $K/make_spec.py $V/data/lerobot/${r}_no_noops_1.0.0_lerobot/meta/episodes.jsonl $k 0 $V/out/subsets/${r}_d${k}_s0.json IPEC-COMMUNITY/${r}_no_noops_1.0.0_lerobot@$rev; done
  done
  for s in d1_s0 d5_s0 d50_s0; do cmp <(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['episodes'])" $K/subsets/$s.json) <(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['episodes'])" $V/out/subsets/libero_spatial_$s.json) && echo "spatial $s identical to the pilot list"; done
}
p_hdf5() {
  cd $V/data/hdf5; mkdir -p libero_spatial
  for t in pick_up_the_black_bowl_between_the_plate_and_the_ramekin_and_place_it_on_the_plate pick_up_the_black_bowl_in_the_top_drawer_of_the_wooden_cabinet_and_place_it_on_the_plate; do
    f=libero_spatial/${t}_demo.hdf5
    if [ ! -f $f ]; then curl -sSfL --limit-rate 40M -o $f.part "https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/resolve/main/$f"; mv $f.part $f; fi
  done
  sha256sum libero_spatial/*.hdf5 | tee $V/data/hdf5/SHA256.txt
}
PH=("$@"); [ ${#PH[@]} = 0 ] && PH=(uv src elb esv data data4 hdf5)
for p in "${PH[@]}"; do run $p p_$p || { ph "FAIL $p"; [ $p = hdf5 ] || exit 1; }; done
ph "SETUP_END"
