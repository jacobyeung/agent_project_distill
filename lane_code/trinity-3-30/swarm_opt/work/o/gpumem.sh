export TZ=UTC
sacct -j 172744,172744.batch -P -n --format=JobID,Elapsed,MaxRSS,ReqTRES%80,TRESUsageInMax%300 2>&1 | head -6
sacct -j 172744 -P -n --format=AllocTRES%120,NodeList 2>&1 | head -2
scontrol show config 2>/dev/null | grep -i -E "AccountingStorageTRES|AcctGatherEnergy|JobAcctGatherType" | head -4
