set +x
cd /scratch/jjyeung
f=devs1_r2/anchors/g3s64/scannet__scene0155_00/A_MANIFEST.json; head -c 2500 $f; echo
f2=$(ls -d devs1_r2/anchors/g3s32/* | head -1); ls $f2; head -c 1200 $f2/A_MANIFEST.json; echo
ls /scratch/jjyeung/orch_n30/fb_pack/k1point/ 2>&1 | head
