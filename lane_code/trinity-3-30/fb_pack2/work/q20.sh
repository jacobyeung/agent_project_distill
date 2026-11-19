cd /scratch/jjyeung/orch_n30/fb_pack && tar cf - k1point | timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cd /scratch/jjyeung/orch_n30/fb_pack && tar xf - && sha256sum k1point/*" 2>&1
F=/scratch/jjyeung/orch_n30/fb_pack; date -u +%TZ; df -h /scratch|tail -1; tmux ls 2>&1 | grep fbp | cut -d: -f1 | tr '\n' ' '; echo
for t in patchA2 prior2b donor2; do echo "== $t $(du -sh $F/$t 2>/dev/null|cut -f1) out: $(ls $F/$t/out | wc -l)"; tail -c 350 $F/$t/STATUS.md 2>/dev/null; echo; done
for t in camformrev pointrec; do echo "== $t $(du -sh $F/$t|cut -f1) $(ls $F/$t | tr '\n' ' ')"; head -c 300 $F/$t/REVIEW_VERDICT.md $F/$t/RECORD.md 2>/dev/null; echo; done
