export TZ=UTC
O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_8417c021
date -u +%FT%TZ
sinfo -p general -o '%n %c %m %C %T' 2>&1 | head -8
for d in $KH/o $IN; do f=$d/.wtest_$$; head -c 65536 /dev/zero > $f && sync && [ $(stat -c %s $f) = 65536 ] && echo "write ok $d" && mv $f $d/.wtest_done3; done
ls -ld $O/r/4d3cd40e $O/r/63e57182 $O/x_f5c353f7 2>&1
cd $IN && sbatch --test-only -J a15_cot_ap0d5e2a71 -o /dev/null -e $KH/o/%j.err a2/ja2.sh 2>&1 | tail -1
sbatch --test-only -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 24:00:00 -J a15_cot_ap0d5e2a71 -o /dev/null --wrap true 2>&1 | tail -1
squeue -u $USER -o '%i %j %P %T %S %l' 2>&1 | grep -v jjy_ | head
df -h /project/community | tail -1
