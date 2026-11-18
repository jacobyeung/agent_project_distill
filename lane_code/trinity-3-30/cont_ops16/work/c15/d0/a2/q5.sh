export TZ=UTC; KH=/project/community/jjyeung/okh7/x_8417c021; J=170109
cd $KH && tar cf - o/$J.a.steps o/$J.steps o/$J.fam.json o/$J.s1.json o/$J.vt.json o/$J.s2.steps $(cd $KH && ls runs/*/inputs/data_receipt.json runs/*/inputs/prepare_*/routing/materialization*.json runs/*/inputs/prepare_*/config.json runs/*/inputs/prepare_*/result.json 2>/dev/null) 2>/dev/null
