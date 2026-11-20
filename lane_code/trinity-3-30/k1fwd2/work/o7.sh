D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a; cd $D
N=985f082abb9ff856/173486/cd89024cbaaac4b50/result.tar.gz; O=/project/community/jjyeung/okh7/b7e31d84a90c62f5/170235/ad2472b1be07d4193/result.tar.gz
cat $(dirname $N)/EXIT.json; echo
timeout 600 /usr/bin/python3 -I -s -B fov_check.py $O $N g_76e2c177ec2a.json /tmp/k1fwd2_canary.json
/usr/bin/python3 -c "
import json;d=json.load(open('/tmp/k1fwd2_canary.json'));[print(r) for r in d['rows']]"
tar tzvf $N | grep -E 'probe/[0-9a-f]{16}/' | head -12
tar xzOf $N metadata/CANARY.json | head -c 600; echo
TZ=UTC squeue -j 173486 -h -o '%T %M'
