#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
X=/scratch/jjyeung/orch_n30/so_xstore/in; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21
T=$W/out/tree_rebuild_b21_b262e7a7.tar
if [[ ! -f $X/tree21b/READY ]]; then
  s=$(nice -n 10 sha256sum $T | cut -d' ' -f1); echo "b21 sha $s"
  if [[ $s == fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59 ]]; then
    mkdir -p $X/tree21b && nice -n 10 tar xf $T -C $X/tree21b && ls $X/tree21b | head
    ls -d $W/work/base/tree_b01ce449 $W/work/build15/inputs $W/work/build_n1/inputs 2>&1
    printf 'build 21 package tree_rebuild_b21_b262e7a7.tar sha256 fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59 seal b262e7a7 (936 files), confirmed by tree_rebuild12 09:03Z (112/112 focused OK with fixtures linked).\nA build 21c (naming fix: opaque staged name for k/benchmark_scene_exclusions.json, scanner over all decoded maps) follows ~10:00Z; port to it only if the lane places it.\nOn a bare untar 37 focused tests error on missing fixture dirs not in the package: work/base/tree_b01ce449, work/build15/inputs, work/build_n1/inputs. Read-only copies: %s/work/ (link them into a copy under $L/work, never write there).\n' $W > $X/tree21b/READY
  fi
fi
cat $X/tree21b/READY 2>/dev/null | head -2 | cut -c1-80
bash $P/poll118o.sh 2>&1 | grep -v "dispatch.*log |"
tail -c 300 /scratch/jjyeung/orch_n30/so_xstore/work/STATUS.md; echo; tail -c 200 /scratch/jjyeung/orch_n30/so_pack_a/work/STATUS.md 2>/dev/null
