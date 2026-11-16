set +e
C=/project/community/jjyeung; O=/home/jjyeung/okit
D=$O/tmp/x27b; mkdir -p $D/r2 $D/r0
tar xf $C/bd8ae51c/p/d59945c1/371be2e2.00 -C $D/r2 --wildcards '*.py' '*.json' '*.sh' '*.md' 2>&1 | tail -2
(cd $D/r2 && find . -type f \( -name '*.py' -o -name '*.sh' \) -size -2M | sort | xargs sha256sum) | head -150
echo "==== r2 file count"; tar tf $C/bd8ae51c/p/d59945c1/371be2e2.00 | wc -l; tar tf $C/bd8ae51c/p/d59945c1/371be2e2.00 | awk -F/ '{print $1"/"$2"/"$3"/"$4}' | sort | uniq -c | sort -rn | head
echo "==== r0 non-env"; cat $O/p/d59945c1/4fe70504.00 $O/p/d59945c1/4fe70504.01 | tar tf - | grep -v '^sj/envs/\|^sj/uv-python/' | head -100
