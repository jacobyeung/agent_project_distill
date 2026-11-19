W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"
grep -n -E "self.home|self.live *=|self.spool *=|add_argument|n_ck|def main" $K/b/pc.py </dev/null | head -20 | cut -c1-220
grep -n -E "pc\.py|sess" $K/job.sh $K/b/*.sh </dev/null | head; ls $W/w24/out | grep b24f
