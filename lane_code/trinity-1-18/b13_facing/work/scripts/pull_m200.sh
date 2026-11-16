set -u
B=/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/kit/build/a4cadd8934b
cd $B || { echo NOBUILD; exit 3; }
ls -la; du -sh . ; find . -maxdepth 7 \( -name 'items_*.jsonl' -o -name ITEMS.jsonl -o -name 'budget_2048*' \) | head -40
S=$(du -sm --exclude='*.tar.gz' . | cut -f1); echo SIZE_MB=$S
[ "$S" -lt 300 ] || { echo TOOBIG; exit 4; }
tar cf - --exclude='*.tar.gz' . | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cd /scratch/jjyeung/orch_n30/b13_facing/work/in/d0_m200_raw && tar xf -"; echo TAR_RC=$?
