export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
cd /project/community/jjyeung/okh7/d9c35d0a || exit 1
date -u +%FT%TZ; ls -la; df -h /project/community | tail -1
which gsutil gcloud
for f in a.tar c.tar; do sha256sum $f; done
for f in a.tar c.tar; do timeout 900 gsutil -q cp $f gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/$f && echo "cp $f ok"; done
gsutil ls -la gs://cmu-gpucloud-jjyeung/q8/d9c35d0a/
squeue -u $USER -o '%i %j %P %T %M %l %S %Q' 2>&1 | head
