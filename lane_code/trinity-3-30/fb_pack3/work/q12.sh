F=/scratch/jjyeung/orch_n30/fb_pack/fov/build2; date -u +%TZ; tmux ls 2>&1 | grep fbp | cut -d: -f1 | tr '\n' ' '; echo; ls $F; tail -c 500 $F/STATUS.md 2>/dev/null
