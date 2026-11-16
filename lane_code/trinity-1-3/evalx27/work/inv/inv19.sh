set +e
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
C=/project/community/jjyeung; O=/home/jjyeung/okit
echo "==== cells"; ls -la $C/cp4tk_eval/eval/cells | grep -i 'f17' | head -30
S=$O/tmp/x27; mkdir -p $S/gs $S/res $S/official $S/f17
timeout 60 gcloud storage cp gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/code_f665b6efa2cdac0c.tar gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/code_4d05c37b29479787.tar $S/gs/ 2>&1 | tail -2
cp $O/evalx_results/e193c2a3c/result.tar.gz $S/res/e193c2a3c_result.tar.gz; cp $O/evalx_results/e193c2a3c/EXIT.json $S/res/e193c2a3c_EXIT.json
cp $O/evalx_results/e3da9a577/EXIT.json $S/res/e3da9a577_EXIT.json
cp $C/cp4tk_eval/official/meta_5130.jsonl $S/official/
cp -r $C/official_reads/tree/official/*.py $C/official_reads/bin $C/official_reads/expect68.json $C/official_reads/VCHECK.json $C/official_reads/status.json $S/official/ 2>&1
cp $C/cp4tk_eval/bin/official/score_and_aggregate.py $S/official/cp4tk_score_and_aggregate.py
(cd $C/official_reads/vview && for d in *; do for f in $d/*; do echo "$f $(readlink $f)"; done; done) > $S/official/vview_links.txt
for d in 3e0e8a36 8b677689; do (cd $C/$d && ls -l */) > $S/official/alias_${d}_ls.txt; done
cd $O/tmp && tar cf x27_pull.tar x27 && sha256sum x27_pull.tar && ls -l x27_pull.tar
