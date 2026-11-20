export TZ=UTC; date -u +%TZ; hostname -s; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
which unshare bwrap; bwrap --version 2>&1; cat /proc/sys/user/max_user_namespaces; timeout 20 unshare -Urm sh -c 'mkdir -p /tmp/$USER.u && mount -t tmpfs -o size=1m tmpfs /tmp/$USER.u && df -h /tmp/$USER.u | tail -1' 2>&1 | tail -2
ls -l $X/jd5.sh; wc -c $X/jd5.sh; df -BG --output=avail /project/community | tail -1
