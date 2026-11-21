W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; A=$W/w24z11b/a_zffhb1q8/armed; S=$W/work/s24m4z12a; date -u +%TZ
test -e $S && { echo EXISTS; exit 1; }; mkdir -p $S
for k in q n n_go; do (cd $A/kits/$k; echo "$k seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) listed $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; comm -23 <(find . -type f | sed 's|^\./||' | sort) <(awk '{print $2}' SHA256SUMS.txt | sed 's|^\*||' | sort)); done
cp -a $A/kits/q $A/kits/n $A/kits/n_go $S/; mkdir -p $S/u; cp -p $A/upload/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73 $S/u/
(cd $S && find . -type f ! -name MANIFEST.sha | sed 's|^\./||' | sort | xargs sha256sum > MANIFEST.sha; wc -l MANIFEST.sha; tar cf $W/work/s24m4z12a.tar . ) && sha256sum $W/work/s24m4z12a.tar && ls -l $W/work/s24m4z12a.tar
diff <(cd $A/kits/n && find . -type f | sort | xargs sha256sum) <(cd $A/kits/n_go && find . -type f | sort | xargs sha256sum) | cut -c1-120
K=$W/w24z12/out/kit_n_go; ls $K $K/b | head -60; wc -c $K/job.sh; cat $K/job.sh | head -80
