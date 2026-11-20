ls -la /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python 2>&1 | head -2
ls /project/community/jjyeung/ | tr '\n' ' ' | head -c 3000; echo
for p in /project/community/jjyeung/envs /project/community/jjyeung/cache /project/community/jjyeung/sj; do ls $p 2>&1 | head -5; done
python3 -m pip --version 2>&1; ls ~/.local/lib 2>&1; python3 -c "import urllib.request,ssl;print('ssl ok')"
module avail 2>&1 | head -20
