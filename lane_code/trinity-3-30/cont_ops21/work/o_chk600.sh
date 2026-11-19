K=/project/community/jjyeung/okh7/x_ee227714; cat $K/o/gcs_6ed2c7aa_m600.done; echo; sha256sum $K/o/gcs_6ed2c7aa_m600.done
sha256sum $K/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json $K/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json $K/runs/6ed2c7aa/inputs/data_receipt.json
/usr/bin/python3 -c "import json;a=json.load(open('$K/runs/6ed2c7aa/m600/artifact.json'));print({k:a[k] for k in a if not isinstance(a[k],(dict,list))})"
/usr/bin/python3 -c "import json;a=json.load(open('$K/runs/6ed2c7aa/m400/artifact.json'));print({k:a[k] for k in a if not isinstance(a[k],(dict,list))})"
TZ=UTC squeue -u jjyeung -h -o '%i %j %P %T %M %N'
