df -h /tmp /project/community | tail -2; nproc; free -g | head -2
V=/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar
time (nice -n 19 ionice -c3 tar -tvf $V | grep -E 'site-packages/tokenizers(-[^/]*)?/?$|site-packages/tokenizers/__init__|bin/python3(\.[0-9]+)?$|tokenizers.*\.so' | head -12)
