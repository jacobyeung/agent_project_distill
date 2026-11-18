export TZ=UTC
K=/project/community/jjyeung/okh7/x_07ca49df
cd $K || exit 1
echo "## ls kit top"; ls -la --time-style=+%FT%TZ $K | head -40
echo "## ls kit b"; ls -la $K/b | head -60
for f in b/c.sh b/gcsput.py b/i.py b/sg.py b/a.py b/r8.py b/g.py b/w.py b/h.py; do echo "@@FILE $f $(stat -c %s $f)"; base64 -w0 < $f; echo; done
echo "## gcs.log"; cat $K/o/gcs.log; echo; for f in $K/o/gcs_469ddece_*.done $K/o/gcs_469ddece_mstop.claim; do echo "-- $f"; cat $f; echo; done
echo "## submission"; cat $K/o/469ddece.GO1518.submission.json; echo; cat $K/o/469ddece.GO1518.stdout
echo "## A.verify.part"; cat /project/community/jjyeung/okh7/r/5da50f2b/A.verify.part
echo "## okh7"; ls -la --time-style=+%FT%TZ /project/community/jjyeung/okh7 /project/community/jjyeung/okh7/j | head -30
echo "## home quota"; quota -vs 2>&1; echo rc=$?; ls -la /home/jjyeung | head -40
echo "## distill okit"; ls -la --time-style=+%FT%TZ /project/community/jjyeung/distill/okit 2>&1 | head -30
echo "## end"
