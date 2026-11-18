export TZ=UTC
for p in advanced preempt general; do scontrol show partition $p | grep -oE '(PartitionName|PriorityTier|PreemptMode|QoS|MaxTime)=[^ ]*' | tr '\n' ' '; echo; done
scontrol show config | grep -iE 'PreemptType|PreemptMode'
squeue -u $USER -h -o '%i|%T|%R' | grep -v jjy_
