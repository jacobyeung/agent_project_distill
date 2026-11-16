set +e
export TZ=UTC
date -u
P=/project/community/jjyeung/okh7/x27ret
mkdir -p $P
echo "== pool write test $P"
timeout 60 bash -c "dd if=/dev/urandom of=$P/.wtest_op bs=1M count=4 conv=fsync 2>&1 | tail -1; sha256sum $P/.wtest_op" ; echo rc=$?
: > $P/.wtest_op
echo "== home pool write test"
timeout 60 bash -c "dd if=/dev/zero of=/home/jjyeung/okit/evalx_results/.wtest_op bs=1M count=4 conv=fsync 2>&1 | tail -1"; echo rc=$?
: > /home/jjyeung/okit/evalx_results/.wtest_op 2>/dev/null
ls -la $P
echo "== queue"; squeue -u jjyeung -o "%.10i %.10P %.28j %.8T %.10M %R"
sinfo -p general -o "%P %a %D %T %G" 2>&1 | head
