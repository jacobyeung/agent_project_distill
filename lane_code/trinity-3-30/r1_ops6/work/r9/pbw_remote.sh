export TZ=UTC; TOK=a5416871
D=/project/community/jjyeung/okh7/h_6ed2c7aa/m600/DONE.json; S=/project/community/jjyeung/okh7/pbs_3aeb20ae.sh
q=$(squeue -h -j 172660 -o %T 2>&1); qrc=$?
if (( qrc != 0 )) && [[ $q != *"Invalid job id"* ]]; then echo "WAIT squeue rc=$qrc $q"; exit 0; fi
[[ -n $q && $q != *"Invalid job id"* ]] && { echo "JOB $q"; exit 0; }
st=$(sacct -n -X -j 172660 -o State%30,ExitCode,End | head -1)
case "$st" in *COMPLETED*|*FAILED*|*CANCELLED*|*TIMEOUT*|*NODE_FAIL*|*OUT_OF_ME*|*PREEMPTED*|*BOOT_FAIL*|*DEADLINE*) ;; *) echo "WAIT sacct '$st'"; exit 0;; esac
echo "LEFT $st"
if [[ -e $D ]]; then echo "DONE_PRESENT $(cat $D)"; exit 0; fi
echo "$(sha256sum $S | cut -c1-64)" | grep -qx 3aeb20ae77d5ae7c1c7161141e1ed489a91602e12fc4994abfcea74c13f2b2ef || { echo "SCRIPT_SHA_DIFFERS"; exit 0; }
[[ -e /project/community/jjyeung/okh7/pb_$TOK ]] && { echo "OUT_EXISTS"; exit 0; }
cat /project/community/jjyeung/okh7/r/6ed2c7aa/A.json 2>&1 | head -2
j=$(sbatch --parsable --job-name=a15_cot_ap$TOK --time=04:00:00 $S 6ed2c7aa 600 /project/community/jjyeung/okh7/pb_$TOK 13800 2>&1); echo "SUBMITTED rc=$? job=$j token=$TOK"
squeue -h -j "${j%%;*}" -o '%i %T %R %S' 2>&1
