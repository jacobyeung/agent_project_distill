W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
NEED="02315a74 3119aa4a a1869ae2 dafa4a9c 600ef69d 99e6eed6 66c427e2 1c7c930d 62113ff3 4701e195 6eb00a2d 8a97fcc4 6add0ad5 43853165 caba6a56 d21e374f d1454a44 d2fd6208 f41d15aa 0d28fdd4 c43379d7 e3ee51da 8957d119 c072905b 7b3d696d 5b584f1d"
for d in $W/w24z15/out/u $W/w24z8/out/u $W/w24z8b/out/u $W/work/s24m4z12a/u $W/work/s24m4z8b/u $W/work/up24/u $W/work/up24k/u $W/work/up24m2/u $W/work/up24m3/u $W/work/up24m3c/u $W/work/x24j/staged /scratch/jjyeung/orch_n30/n_review/r1j/div $W/w24z12/inputs $W/w24z11b/inputs $W/w28fix/work $W/w28fix/src; do
  n=$(ls $d 2>/dev/null | wc -l); hits=""
  for s in $NEED; do f=$(ls $d 2>/dev/null | grep "^$s" | head -1); [ -n "$f" ] && hits="$hits $s"; done
  echo "$d n=$n hits:$hits"
done
ls /scratch/jjyeung/orch_n30/n_review/r1j/div | head -40
cat /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/receipt.json; echo; cat /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/MANIFEST.json; echo
ls -la $W/w24z11b/out | head -30; ls $W/w24z12/out $W/w24z12/work | head -40
ls $W/w28fix/work | head -40
