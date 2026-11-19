P=/project/community/jjyeung/okh7/a15_cot_apda6f7936c1779/a
cat $P/0.json; echo; echo ====1; cat $P/1.json; echo; echo ====10; cat $P/10.json; echo; cat $P/9.txt $P/8.txt $P/1.txt; echo
echo ====cfg; python3 - <<'PY'
import json
c=json.load(open('/project/community/jjyeung/okh7/a15_cot_apda6f7936c1779/a/e/7'))
for k in ('code','preparation','init_artifact','depth_init','base_identity','trainer','tree','depth_fov_source','streams','model','align'):
    print(k, json.dumps(c.get(k))[:600])
print(sorted(c.keys()))
r=json.load(open('/project/community/jjyeung/okh7/a15_cot_apda6f7936c1779/a/e/8'))
for k in ('model','trainer_commit','config_sha256','source_seal','init_artifact','depth_init','schema'):
    print('R',k, json.dumps(r.get(k))[:600])
PY
