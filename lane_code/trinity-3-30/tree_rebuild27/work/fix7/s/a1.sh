set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w29f7; mkdir -p $W/t; cd $W
TAR=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix/n_go/k/t_e047002134f979bd.tar
sha256sum $TAR
[ -f $W/t/student_pilot/carrier_c1_run.py ] || tar xf $TAR -C $W/t
ls $W/t | head -3; sha256sum $W/t/student_pilot/carrier_c1_run.py $W/t/student_pilot/c1_pose_mix.py $W/t/student_pilot/carrier_c1_data.py
cat > $W/a1.py <<'PY'
__A1__
PY
date -u +%TZ
R=$(ls /scratch/jjyeung/orch_n30/n_review/r1j/div/*601.jsonl)
nice -n 10 python3 -I -B $W/a1.py $W /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite /scratch/jjyeung/orch_n30/n_review/r1j/div/f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5 /scratch/jjyeung/orch_n30/n_review/r1j/div/0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad $R 2>&1
date -u +%TZ
