P=/project/community/jjyeung/okh7
cd $P/b7e31d84a90c62f5 && ls -la | head -40
S=a7e31d84.d1553118.sh; wc -c $S; sha256sum $S | cut -c1-16
grep -n "m544\|1d6eeb28\|artifact\|heads\|gs://\|ckpt\|checkpoint\|SBATCH\|tmp\|export" $S | cut -c1-250 | head -80
echo "== m400 pkg"; ls -la $P/a15_cot_apda6f7936c1779/a $P/a15_cot_apda6f7936c1779/a/e 2>&1 | head -30
stat -c '%n %s %h %i' $P/a15_cot_apda6f7936c1779/a/e/* $P/a15_cot_apfadf2291c654b/a/e/* $P/a15_cot_apdc76460c3a164/a/e/* 2>&1
df -h $P | tail -1
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %N %R %b' 2>&1
TZ=UTC sinfo -p advanced -N -o '%N %G %t %C' 2>&1 | head
