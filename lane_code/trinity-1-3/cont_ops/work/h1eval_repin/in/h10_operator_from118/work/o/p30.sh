export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; D=/project/community/jjyeung/b01ec87a6f29b
cd $D
Q=$(squeue -u jjyeung -p general -h -o '%i %j %T'); echo "general-ours: [$Q]"; [ -n "$Q" ] && { echo REFUSE; exit 1; }
sha256sum $W/1_t3.json | grep -q 1abaf6ca0ebcf7a710292b5d337a59534a5a7ed178c48965a5530da5f9fd041f || { echo BAD1; exit 1; }
cp $W/1_t3.json a/1.json && chmod 600 a/1.json && sha256sum 0.tgz PACKAGE.json a/1.json
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 03:00:00 > /dev/null; echo "check rc=$?"
A_N=1 A_T=03:00:00 bash SUBMIT.cmd; echo "submit rc=$?"
sleep 20; squeue -u jjyeung -p general -o '%i %j %T %M %l %b %r'
