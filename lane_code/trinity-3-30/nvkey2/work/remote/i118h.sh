echo "== $(hostname -s) $(date -u +%T)"
W=/scratch/jjyeung/orch_n30/sb_mask_phrase
ls $W $W/work 2>&1 | head -40
du -sb $W/work/caps 2>/dev/null; ls $W/work/caps | wc -l; ls $W/work/caps | head -3
S=$(du -sb $W/work/caps | cut -f1)
if [ "$S" -lt 2000000000 ]; then
  cd $W/work && nice -n 19 tar cf - caps | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/nvkey1/work/v2/noprop && tar xf - -C /scratch/jjyeung/orch_n30/nvkey1/work/v2/noprop && du -sh /scratch/jjyeung/orch_n30/nvkey1/work/v2/noprop && ls /scratch/jjyeung/orch_n30/nvkey1/work/v2/noprop/caps | wc -l'
  echo "tar rc ${PIPESTATUS[*]}"
else echo "TOO BIG $S"; fi
