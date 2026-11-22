set -u
P=/project/community/jjyeung/b9ef552934627
ls -la $P $P/a $P/a/c $P/a/f 2>&1 | head -60
cd $P && sha256sum 0.tgz 0.json BATCH.sh 3.py CONFIG.json PACKAGE.json a/1.json a/5.py a/6.py a/export.json a/c/CPU.json 2>&1
for f in /project/community/jjyeung/okh7/e6fc152498/e/0 /project/community/jjyeung/okh7/e6fc152498/e/1 /project/community/jjyeung/okh7/e6fc152498/e/2 /project/community/jjyeung/okh7/e6fc152498/e/3 /project/community/jjyeung/okh7/e6fc152498/g/0 /project/community/jjyeung/okh7/e6fc152498/a2.tar /project/community/jjyeung/okh7/e6fc152498/a4.tar /project/community/jjyeung/okh7/e6fc152498/a3.tar; do stat -c '%s %n' $f 2>&1; done
du -sm /project/community/jjyeung/okh7/ae71c903 2>&1 | tail -1
ls /project/community/jjyeung/okh7/ae71c903 2>&1 | wc -l
df -h /project/community/jjyeung 2>&1 | tail -1
/usr/bin/python3 -V
TZ=UTC squeue -u jjyeung -h -o '%i %j %P %T %M %l' 2>&1 | head
TZ=UTC sacct -j 171253,171244 -X -n -P -o JobID,State,Elapsed,NodeList 2>&1
