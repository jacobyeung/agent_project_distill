set +e
quota -s 2>&1 | head -20
du -sh /home/jjyeung 2>/dev/null
du -sh /home/jjyeung/okit/tmp/* 2>/dev/null
touch /home/jjyeung/okit/tmp/.qprobe_x27 && echo WRITE_OK; ls -la /home/jjyeung/okit/tmp/.qprobe_x27
