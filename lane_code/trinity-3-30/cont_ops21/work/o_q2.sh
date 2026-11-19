cd /project/community/jjyeung/okh7
for t in dc863c3e6b41d dacd91c2f5c4b; do P=a15_cot_ap$t; echo "== $t"; ls $P/a/c 2>&1 | head; cat $P/a/1.txt 2>&1; ls $P/a/8.txt 2>&1; done
scontrol show node orchard-community-1 | grep -E "CfgTRES|AllocTRES|Partitions|Gres"
for j in 173241 173242 173243 173234; do scontrol show job $j | grep -E "JobId|TRES=|Partition|QOS" | tr '\n' ' '; echo; done
TZ=UTC sacct -j 173060,172744 -o JobID,State,Elapsed,ReqCPUS,ReqMem,MaxRSS,TotalCPU,NodeList -P | head
sinfo -p advanced -o "%P %D %N %G %T" ; sinfo -p general -o "%P %D %N %G %T"
