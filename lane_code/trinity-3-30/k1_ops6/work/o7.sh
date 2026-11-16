export TZ=UTC
date -u +%FT%TZ
scontrol show node orchard-flame-0 2>&1 | grep -iE "Gres=|CfgTRES|AllocTRES|State=|AvailableFeatures" | head -6
scontrol show node orchard-community-3 2>&1 | grep -iE "Gres=|CfgTRES|AllocTRES|State=|AvailableFeatures" | head -6
echo "--- flame/preempt free GPUs per node"
for n in $(sinfo -h -p flame -o '%n' | sort -u | head -32); do scontrol show node $n | awk -v n=$n '/CfgTRES/{c=$0} /AllocTRES/{a=$0} END{print n, c, a}'; done 2>/dev/null | sed -E 's/CfgTRES=cpu=[0-9]+,mem=[^,]+,billing=[0-9]+,//; s/AllocTRES=//' | head -40
echo "--- pending in preempt/flame"; squeue -p preempt,flame -t PD -h | wc -l; squeue -p preempt,flame -t R -h | wc -l
echo "--- preempt config"; scontrol show partition preempt 2>&1 | grep -iE "PreemptMode|PriorityTier|QoS" | head -4; scontrol show config 2>/dev/null | grep -iE "^PreemptMode|^PreemptType" 
