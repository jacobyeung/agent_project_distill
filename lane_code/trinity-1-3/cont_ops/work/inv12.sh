set -u
export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
timeout 120 gcloud storage cat -r 4290310656-4290312449 'gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar.part00-of-04#1794665056278014' > /tmp/jjy_fw.$$ 2>/tmp/jjy_fw_err.$$; echo "cat rc=$?"; head -c 300 /tmp/jjy_fw_err.$$
echo "FW_SHA $(sha256sum < /tmp/jjy_fw.$$ | cut -c1-64) $(stat -c %s /tmp/jjy_fw.$$)"
echo "FW_BEGIN"; cat /tmp/jjy_fw.$$; echo; echo "FW_END"
