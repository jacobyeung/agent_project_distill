export TZ=UTC
for j in 167857 167858 167859 167860 167861 168278 167894 167739; do scontrol show job $j 2>/dev/null | tr ' ' '\n' | grep -E '^(JobId|JobName|Dependency|Reason|SubmitTime|TimeLimit|TRES)=' | tr '\n' ' '; echo; done
echo "## preempted candidates"; squeue -j 167377,167378,167379,169973 -o '%.10i %.10u %.12P %.20j %.8T %.10M %.12l %N' 2>&1
echo "## deps"; for d in $(scontrol show job 167857 2>/dev/null | tr ' ' '\n' | sed -n 's/^Dependency=//p' | tr ',:?' '\n\n\n' | grep -E '^[0-9]+' ); do squeue -h -j $d -o '%i %u %P %j %T %M %l' 2>&1; sacct -n -X -j $d -o JobID,User,State,End 2>&1 | head -2; done
echo "## node1"; scontrol show node orchard-community-1 2>/dev/null | grep -E 'CfgTRES|AllocTRES|State=' ; squeue -w orchard-community-1 -o '%.10i %.10u %.12P %.8T %.10M %.12l %b' 2>&1
echo "## end"
