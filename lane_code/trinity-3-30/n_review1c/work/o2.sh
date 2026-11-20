cd /project/community/jjyeung/okh7/x_22c714e1 || exit 1
for f in j.sh jd.sh jd2.sh dbb2.py jr.sh jrw.sh; do echo "@@@ $f $(sha256sum < $f|cut -c1-64)"; cat $f; done
ls -la j | tail -5; ls -la u | wc -l; ls -la u | grep -i eac5
