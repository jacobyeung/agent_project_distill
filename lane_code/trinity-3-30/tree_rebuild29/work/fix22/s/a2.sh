W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W || exit 1
L="w24y2/out/rcj w24z11b/out/ARM_LAUNCH_24M4Z11.md w24z11b/out/ARM_LAUNCH_24M4Z11B.md w24z11b/out/ARM_ROUTING_USAGE.md work/TASKA_PASS_0212Z.md work/arm_0216Z.log work/d173881 work/d173912"
du -sc $L >&2
tar czf - $L
