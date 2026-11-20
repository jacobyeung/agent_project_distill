W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24c/work/tree_r1; cd $T; date -u +%TZ
grep -rn "moved_to_vqa_store" --include=*.py . | grep -v "^./tests/" | cut -c1-400
echo "@@KIT"; grep -n "moved_to_vqa_store\|vqa_store" $W/w24e/out/kit_qd/b/*.py | cut -c1-300 | head
