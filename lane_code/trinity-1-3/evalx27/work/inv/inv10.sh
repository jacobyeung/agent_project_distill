set +e
export TZ=UTC
sacct -j 169526,169792,169493 -X -o JobID,SubmitLine%400 -P 2>&1
cat /project/community/jjyeung/gcloud/configurations/config_default
which gcloud gsutil 2>&1
ls /project/community/jjyeung/cp4tk_rt /project/community/jjyeung/cp4tk_rt/kit /project/community/jjyeung/official_reads 2>&1 | head -60
