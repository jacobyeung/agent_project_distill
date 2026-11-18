export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; BUN=$O/i_1be16f28; KH=$O/x_3fdda0fb; PART=${PART:-advanced}
squeue -u jjyeung -n a15_cot_ap8c74b291 -h | grep -q . && { echo "proof already queued"; exit 3; }
grep -q '"status":"CLEAN"' $KH/ANON_OK.json 2>/dev/null || { echo "KH not certified"; exit 3; }
printf '%s  %s\n' 3814df676f9e2090057da9c3989b459fb51badbaef9368026e8c1401f2613e48 "$BUN/a_8c74b291.sh" | sha256sum -c - || exit 3
cd /tmp
PROOF_JOB=$(TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap8c74b291 -o "$KH/o/%j.proof.out" -e "$KH/o/%j.proof.err" -A mt01 -p $PART -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue "$BUN/a_8c74b291.sh"); rc=$?
echo "sbatch rc=$rc PROOF_JOB=${PROOF_JOB%%;*}"
squeue -u jjyeung -o '%i %j %P %T %R %b'
