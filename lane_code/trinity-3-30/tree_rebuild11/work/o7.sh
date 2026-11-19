export TZ=UTC; date -u +%TZ
IN=/project/community/jjyeung/distill/okit/in; ls -la $IN | head -20
P=$(ls -d /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_* | head -1); echo P=$P
find $P -maxdepth 3 -type f -size -5M -name '*.json' 2>/dev/null | while read f; do echo "$(sha256sum < $f | cut -c1-64) $(stat -c %s $f) $f"; done | head -60
