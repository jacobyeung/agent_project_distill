W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W && ls prompts/build16.md inputs/drv_cp | head -3
date -u +%TZ; tmux ls | grep tr10; tail -c 800 $W/w15/work/build15/STATUS.md; ls $W/w15/out | grep -i 15; free -g | sed -n 2p
