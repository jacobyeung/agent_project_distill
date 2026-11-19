cd /project/community/jjyeung/okh7/x_22c714e1 || exit 1
ls -la u/4e8e6c04* u/ca0616db* 2>&1 | head
f=$(ls u/4e8e6c04* 2>/dev/null | head -1); [ -n "$f" ] && { stat -c '%s %y' $f; head -c 100 $f | od -An -tx1 | tr -d ' \n'; echo; tail -c +101 $f | sha256sum; sha256sum $f; }
ls -la o/ | tail -5
