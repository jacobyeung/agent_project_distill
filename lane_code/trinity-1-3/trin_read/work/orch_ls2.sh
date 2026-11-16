export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
timeout 200 gcloud storage ls -l 'gs://cmu-gpucloud-jjyeung/**' 2>/dev/null | grep -E 'f2ad01ad|49becb79|bdad3598|f17|m200' | head -60
echo ===
ls -la /project/community/jjyeung/ | grep -E 'f2ad01ad|49becb79|bdad3598|f17' ; ls -la /home/jjyeung/okit/ 2>/dev/null | head -30
ls -l /project/community/jjyeung/cp4tk_rt/kit/ 2>/dev/null | head -30
