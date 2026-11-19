set -u
R=/scratch/jjyeung/orch_n30/b10_reserve
echo ---FRAMES
ls $R/frames/scannetpp | head -3
S=$(ls $R/frames/scannetpp | head -1)
ls $R/frames/scannetpp/$S | head -5; ls $R/frames/scannetpp/$S | wc -l
ls $R/out/frame_manifests | head -3
head -c 700 $R/out/frame_manifests/$(ls $R/out/frame_manifests | head -1); echo
head -c 600 $R/out/FRAMES_MANIFEST.json; echo
echo ---R0Q
head -c 900 $R/out/qsets/R0_QUESTIONS_dev_f32.jsonl; echo
du -sh $R/frames 2>/dev/null
echo ---B05
P=/scratch/jjyeung/orch_n30/b05_owngrd
ls $P/work/x118 2>&1 | head -20
cat $P/work/x118/launch_teacher.sh 2>&1 | head -40
ls $P/work/x118/*.json 2>/dev/null | head; for f in $P/work/x118/*settings*.json $P/work/*settings*.json; do [ -f "$f" ] && { echo $f; cat $f; echo; }; done
ls -d /scratch/jjyeung/envs/sam3_capretry_native_v1 /scratch/jjyeung/k1_frames 2>&1
ls $P/code/owngrd/ 2>&1 | tr '\n' ' '
echo ---GPU
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1 | head -10
