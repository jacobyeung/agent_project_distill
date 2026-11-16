set +e; export TZ=UTC
ls -la /home/jjyeung/okit/ | head -40
for f in $(find /home/jjyeung/okit -maxdepth 5 -name 'camera_leg.py' 2>/dev/null | head -10); do sha256sum $f; done
ls -la /project/community/jjyeung/cp4tk_f17/
gcloud storage ls 'gs://cmu-gpucloud-jjyeung/q9/f2ad01ad/' 2>&1 | head -30
