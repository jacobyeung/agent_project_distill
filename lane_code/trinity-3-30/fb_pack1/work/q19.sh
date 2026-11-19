F=/scratch/jjyeung/orch_n30/fb_pack; tmux ls 2>&1 | grep fbp | cut -c1-20 | tr '\n' ' '; echo; ls -la $F/camrev; head -c 2500 $F/camrev/REVIEW_VERDICT.md 2>/dev/null
