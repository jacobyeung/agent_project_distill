cd /scratch/jjyeung/orch_n30/lever8/j1/out || exit 1
cat detect/stderr_20261122T110905Z/pass.err | cut -c1-300
du -sb detect
(cd detect && find . -type f -print0 | sort -z | xargs -0 sha256sum) > /tmp/j1_detect_sums_013.txt; sha256sum /tmp/j1_detect_sums_013.txt
tar cf - detect | ssh -o ConnectTimeout=20 trinity-2-28.ib "cd /scratch/jjyeung/orch_n30/lever8/j1/out && tar xf - && cd detect && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum"
echo rc=$?
