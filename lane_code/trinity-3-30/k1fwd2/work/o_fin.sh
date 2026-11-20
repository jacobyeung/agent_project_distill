D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a; cd $D
TZ=UTC sacct -j 173486 -X -n --format=State,Start,End,Elapsed,ExitCode
ls -la 985f082abb9ff856/173486/
N=$(ls -td 985f082abb9ff856/173486/a*/ | head -1)result.tar.gz; echo "FINAL=$N"; ls -la $N; cat $(dirname $N)/EXIT.json; echo
tar xzOf $N COMPLETE.json; echo; tar tzf $N | grep -c 'fov.npz$'; tar tzf $N | grep -c 'own.npz$'
timeout 900 /usr/bin/python3 -I -s -B fov_check.py /project/community/jjyeung/okh7/b7e31d84a90c62f5/170235/ad2472b1be07d4193/result.tar.gz $N g_76e2c177ec2a.json FOV_CHECK.json o_985f082abb9ff856.tar sj/b87008007397.json
sha256sum FOV_CHECK.json
timeout 900 /usr/bin/python3 -I -s -B sel.py $N g_76e2c177ec2a.json 0 FOV_CHECK.json | tee >(sha256sum > /tmp/k1fwd2_sel.sha) | wc -c; sleep 2; cat /tmp/k1fwd2_sel.sha
