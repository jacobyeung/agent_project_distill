set -uo pipefail
export TZ=UTC; O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_f5c353f7
date -u +%FT%TZ
[ "$(sha256sum < $IN/b5/jb.sh | cut -c1-8)" = 3b8f0162 ] && [ "$(sha256sum < $KH/SHA256SUMS.txt | cut -c1-8)" = 231c98dc ] && [ ! -e $O/r/63e57182 ] || { echo "precondition failed"; exit 3; }
squeue -u $USER -p advanced -o '%i %j %T %S %b' 2>&1 | grep -v jjy_
cd $IN && env -u TK_JOB_START sbatch --test-only -J a15_cot_apddbe32d7 -o /dev/null -e $KH/o/%j.err b5/jb.sh 2>&1 | head -1
cd $IN && env -u TK_JOB_START sbatch -J a15_cot_apddbe32d7 -o /dev/null -e $KH/o/%j.err b5/jb.sh 2>&1
sleep 15; squeue -u $USER -o '%i %j %P %T %S %l %b' 2>&1 | grep a15_cot_ap
df -h /project/community | tail -1
