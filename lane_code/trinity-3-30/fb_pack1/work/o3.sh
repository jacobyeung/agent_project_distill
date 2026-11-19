cd /project/community/jjyeung || exit 1
ls -la distill/okit/in/cr/rb_61aebb2b2fca.tar
cd okh7/x_ee227714/k && for f in *.json; do s=$(stat -c %s $f); [ $s -lt 3000000 ] && c=$(grep -c kr9c $f) && [ "$c" != 0 ] && echo "$f $s kr9c=$c"; done
sha256sum *.json 2>/dev/null | grep -i "^47c9206e\|^61aebb2b" 
