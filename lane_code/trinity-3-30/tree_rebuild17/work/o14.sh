P=/project/community/jjyeung/okh7/x_ee227714; X=/project/community/jjyeung/okh7/x_22c714e1; H=eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9
grep -n "pool_selection_eac5f9f0" $P/SHA256SUMS.txt | head -3; sha256sum $P/SHA256SUMS.txt | cut -c1-16
test -e $X/u/$H && echo "U EXISTS" || { cp $P/k/pool_selection_eac5f9f0.json $X/u/.$H.tmp && [ "$(sha256sum $X/u/.$H.tmp | cut -c1-64)" = $H ] && chmod 400 $X/u/.$H.tmp && mv $X/u/.$H.tmp $X/u/$H && echo "U COPIED"; }
ls -la $X/u/$H
echo BEGIN64; base64 -w0 $P/k/pool_selection_eac5f9f0.json; echo; echo END64
