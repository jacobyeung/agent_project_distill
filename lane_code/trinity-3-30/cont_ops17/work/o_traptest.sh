set -euo pipefail; umask 077
P=/project/community/jjyeung/okh7/a15_cot_apb635a315de01e; S=/project/community/jjyeung/okh7/813f42db/r9
test "$(cat $P/a/1.txt)" = 0
/usr/bin/python3 - $P/BATCH.sh $S/trap_test.sh <<'PY'
import sys
b=open(sys.argv[1]).read(); head,rest=b.split("<<'A' &\n",1); body,tail=rest.rsplit("\nA\n",1)
open(sys.argv[2],'w').write(head+"<<'A' &\nprint('trap test: reader replaced by this line')\nA\n"+tail)
PY
J=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=1G --time=00:05:00 --job-name=a15_cot_ap1ed4e44538f0 --export=NONE --no-requeue --chdir=/tmp --output=/dev/null --error=/dev/null $S/trap_test.sh); echo "$J" > $S/traptest.txt; echo trap test job $J
