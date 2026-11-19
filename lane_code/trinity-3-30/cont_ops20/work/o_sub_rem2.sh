set -uo pipefail
TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T %M"
P=/project/community/jjyeung/okh7/a15_cot_apd5b7ea08426cd T=01:30:00 bash /project/community/jjyeung/okh7/813f42db/r544c/o_sub_D.sh; echo rc=$?
echo JOB $(cat /project/community/jjyeung/okh7/a15_cot_apd5b7ea08426cd/a/8.txt 2>/dev/null)
