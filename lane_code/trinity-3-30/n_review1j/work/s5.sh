T=/scratch/jjyeung/orch_n30/n_review/r1j/t; C=$T/student_pilot
sed -n 55,88p $C/c1_pose_mix.py < /dev/null
echo "== 405-422 run"; sed -n 405,421p $C/carrier_c1_run.py < /dev/null
echo "== pinned def"; grep -n "^def pinned\|^def load\b\|^def load(" $C/p3_provenance.py $C/carrier_c1_run.py < /dev/null
n=$(grep -n "^def pinned" $C/p3_provenance.py < /dev/null | cut -d: -f1); sed -n "${n},$((n+25))p" $C/p3_provenance.py < /dev/null
echo "== where does N vqa mirror live"; ls -d /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa 2>&1; ls /scratch/jjyeung/n30_mirror 2>&1 | head
