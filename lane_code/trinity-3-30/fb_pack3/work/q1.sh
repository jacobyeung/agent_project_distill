F=/scratch/jjyeung/orch_n30/fb_pack; date -u +%TZ; df -h /scratch|tail -1; tmux ls 2>&1 | grep fbp | cut -d: -f1 | tr '\n' ' '; echo
for t in patchA2rev donor3rev camform2rev; do echo "== $t $(ls $F/$t | tr '\n' ' ') log=$(stat -c %s $F/$t/cursor.log 2>/dev/null)"; head -c 600 $F/$t/REVIEW_VERDICT.md 2>/dev/null; echo; done
echo "== prior2c out: $(ls $F/prior2c/out 2>/dev/null | tr '\n' ' ')"; tail -c 400 $F/prior2c/STATUS.md 2>/dev/null; echo
