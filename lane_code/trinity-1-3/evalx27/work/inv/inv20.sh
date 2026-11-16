set +e
C=/project/community/jjyeung
echo "==== camera archive"; sha256sum $C/bd8ae51c/p/d59945c1/5e297c41.tar; tar tvf $C/bd8ae51c/p/d59945c1/5e297c41.tar | awk '{print $3,$6}' | head -150
echo "==== runtime_2 top"; tar tf $C/bd8ae51c/p/d59945c1/371be2e2.00 | awk -F/ '{print $1"/"$2"/"$3"/"$4"/"$5}' | sort -u | head -40
echo "==== runtime_0 top"; cat /home/jjyeung/okit/p/d59945c1/4fe70504.00 | tar tf - 2>/dev/null | awk -F/ '{print $1"/"$2"/"$3"/"$4}' | sort -u | head -30
echo "==== k6tk"; ls $C/cp4tk_fr/k6tk | head; ls $C/cp4tk_fr/k6tk | wc -l
