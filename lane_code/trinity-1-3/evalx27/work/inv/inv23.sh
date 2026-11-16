set +e
C=/project/community/jjyeung; O=/home/jjyeung/okit
D=$O/tmp/x27c
mkdir -p $D/f17
for c in f17ref_vsi f17tk_vsi; do (cd $C/cp4tk_eval/eval/cells && find $c -type f -size -5M) ; done > $D/f17/list.txt
(cd $C/cp4tk_eval/eval/cells && tar cf $D/f17/cells.tar -T $D/f17/list.txt)
wc -l $D/f17/list.txt; head -40 $D/f17/list.txt
cd $D && find . -type f -size -5M > $O/tmp/x27c_list.txt && wc -l $O/tmp/x27c_list.txt
tar czf $O/tmp/x27c.tar.gz -T $O/tmp/x27c_list.txt && ls -l $O/tmp/x27c.tar.gz && sha256sum $O/tmp/x27c.tar.gz
