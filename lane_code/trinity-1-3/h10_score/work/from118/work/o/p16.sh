cd /project/community/jjyeung/b01ec87a6f29b && sha256sum a/1.json /project/community/jjyeung/okh7/e6fc152498/a3.tar && stat -c '%a %n' a
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 4 --time 01:15:00; echo "check rc=$?"
