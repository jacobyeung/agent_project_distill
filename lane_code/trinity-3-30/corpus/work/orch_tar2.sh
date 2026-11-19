set -u
cd /project/community/jjyeung/okh7 || exit 1
nice -n 10 tar cf cc886a29e4ef/r.tar -T cc886a29e4ef/files.txt && sha256sum cc886a29e4ef/r.tar > cc886a29e4ef/r.tar.sha256 && ls -l cc886a29e4ef/r.tar && cat cc886a29e4ef/r.tar.sha256
timeout 600 gsutil -q cp cc886a29e4ef/r.tar gs://cmu-gpucloud-jjyeung/q8/cc886a29e4ef/r.tar && gsutil ls -l gs://cmu-gpucloud-jjyeung/q8/cc886a29e4ef/r.tar
