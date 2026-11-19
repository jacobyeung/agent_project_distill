export TZ=UTC; date -u +%TZ; O=/project/community/jjyeung/okh7; IN=/project/community/jjyeung/distill/okit/in
ls -la $IN | tail -n +21 | head -30
tar tvf $IN/c_fa8681cba4c0.tar | head -30
for d in $O/7c9f2d84 $O/7c9f2d84_in $O/7c9f2d84_bundle; do echo "== $d"; find $d -maxdepth 4 -type f -size -5M 2>/dev/null | head -40 | while read f; do echo "$(sha256sum < $f | cut -c1-16) $(stat -c %s $f) $f"; done; done
