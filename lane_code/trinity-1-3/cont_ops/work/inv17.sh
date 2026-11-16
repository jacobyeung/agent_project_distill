O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_7cb63d1e
date -u
for d in $KH/o $IN; do f=$d/.wtest_$$; head -c 65536 /dev/zero > $f && sync && [ $(stat -c %s $f) = 65536 ] && echo "write ok $d" && mv $f $d/.wtest_done; done
ls -la $KH/o | head
cd /tmp && TZ=UTC sbatch --test-only -o /dev/null -e $KH/o/%j.err < $IN/ja.sh 2>&1 | tail -2
TZ=UTC squeue -p general -u jjyeung -o '%.10i %.20j %.8T %S' 2>&1
TZ=UTC squeue -p general -o '%.10i %.9u %.20j %.8T %.10M %.12l %S' 2>&1 | head -14
df -h /project/community | tail -1; df -h /tmp | tail -1
