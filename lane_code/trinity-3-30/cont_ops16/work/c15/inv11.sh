set -u
export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
timeout 120 gcloud storage cat -r 4290310656-4290312449 'gs:///q8/8865619b/469ddece_mstop.tar.part00-of-04#1794665056278014' > /tmp/jjy_fw.$$ 2>/tmp/jjy_fw_err.$$; echo "cat rc=$?"; head -c 300 /tmp/jjy_fw_err.$$
echo "FW_SHA $(sha256sum < /tmp/jjy_fw.$$ | cut -c1-64) $(stat -c %s /tmp/jjy_fw.$$)"
echo "FW_BEGIN"; cat /tmp/jjy_fw.$$; echo; echo "FW_END"
/usr/bin/python3 -I - <<'PY'
import tarfile, hashlib, json
out = {}
with tarfile.open('/project/community/jjyeung/distill/okit/in/e00') as t:
    for m in t:
        if m.isfile():
            out[m.name] = hashlib.sha256(t.extractfile(m).read()).hexdigest()
print('SMALL_BEGIN'); print(json.dumps(out, sort_keys=True)); print('SMALL_END')
PY
