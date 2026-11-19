ls /project/community/jjyeung/okh7/ae71c903 /project/community/jjyeung/okh7/ae71c903_fetched | grep cb2b
P=/project/community/jjyeung/okh7/a15_cot_apcb2b4d58630bc; RT=cb2b4d58630bc$(printf '%08x' $(cat $P/a/8.txt)); SP=/project/community/jjyeung/okh7/ae71c903; test -d $SP/$RT && ! test -e ${SP}_fetched/$RT && mv $SP/$RT ${SP}_fetched/$RT && echo "moved $RT"
for d in $SP/*/; do find $d -type f -printf "%s\n"; done | awk '{s+=$1} END {print "pool bytes", s}'
echo == D remainder submit
TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T"
P=/project/community/jjyeung/okh7/a15_cot_apd09f959256d87 T=01:30:00 bash /project/community/jjyeung/okh7/813f42db/r544b/o_sub_D.sh 2>&1 | tail -4
