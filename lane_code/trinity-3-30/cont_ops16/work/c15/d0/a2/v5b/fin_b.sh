set -uo pipefail
export TZ=UTC; O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_f5c353f7
date -u +%FT%TZ
[ -e $KH/ANON_OK.json ] && mv $KH/ANON_OK.json $KH/o/ANON_OK.placeholder.json
cat > $KH/ANON_OK.json <<'J'
{"external":[{"path":"/project/community/jjyeung/okh7/i_bb09a77d/vb5.json","sha256":"c95023e46d9171071c7cb738367dae115bebaf4a6519931ec514d20e68ffa5d8"},{"path":"/project/community/jjyeung/okh7/i_bb09a77d/b5/4.json","sha256":"3f64925ab47ef60416ac574c806aabad5d4f3ecc6bab51503968eb10befdf9d7"},{"path":"/project/community/jjyeung/okh7/i_bb09a77d/b5/full_weights.json","sha256":"211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302"},{"path":"/project/community/jjyeung/okh7/i_bb09a77d/b5/jb.sh","sha256":"3b8f0162cba302e06aea764d1b876689938dc26595e8bbda16d95739d09964e8"},{"path":"/project/community/jjyeung/okh7/i_bb09a77d/b5/over.json","sha256":"70bbb61e876bd3883c6eb6fb83ae245f88911b3bd2a3751245bacfb9a9a8669c"},{"path":"/project/community/jjyeung/okh7/i_bb09a77d/b5/review.json","sha256":"ddd34ff2dadf204960306d960ca039f417ebed93bd62957955479add9f595927"},{"path":"/project/community/jjyeung/okh7/i_bb09a77d/b5/staging.json","sha256":"133bffea4c9320fa747f7d6275f43b64ed57cf31fc6c95314fc811721b9100cf"}],"hits":0,"manifest_sha256":"231c98dcc568b4a1d5123bd827c50c7e651dffa602141670e1716c9ce2fc61ae","scope":"Eight new or changed fixture records, six listed b5 bundle files, and the shared job receipt. Round-11 changed content was scanned; unchanged content retains the round-10 review. Final Orchard records must match fixture manifest a40b3d8c1be8ef3b83b8a7182b187ed3fc40525e1d4cae0aee108be48e442da8 except launch.json status=READY and production_authorized=true, with its manifest hash updated accordingly. Both locally absent payload entries must retain their sealed hashes. Inherited identifiers and Python split/rsplit calls are count-only. Row-store contents are excluded under the supplied exception. Content certification does not grant submission authorization.","status":"CLEAN"}
J
chmod 600 $KH/ANON_OK.json; sha256sum $KH/ANON_OK.json $KH/SHA256SUMS.txt $IN/vb5.json $IN/b5/*.json $IN/b5/jb.sh
cd $IN && /usr/bin/python3 -I -c 'import sys; sys.path.insert(0, sys.argv[1] + "/b"); import a; c = a.main(sys.argv[1]); print("a.py PASS", c["status"])' $KH 2>&1 | tail -2
ls -l $KH/sess.json; for d in $KH/o; do f=$d/.wtest_$$; head -c 65536 /dev/zero > $f && sync && [ $(stat -c %s $f) = 65536 ] && echo "write ok $d" && mv $f $d/.wtest_done; done
ls -ld $O/r/63e57182 2>&1
cd $IN && env -u TK_JOB_START sbatch --test-only -J a15_cot_apddbe32d7 -o /dev/null -e $KH/o/%j.err b5/jb.sh 2>&1
squeue -u $USER -o '%i %j %P %T %S %l' 2>&1 | grep -v jjy_ | head
df -h /project/community | tail -1
